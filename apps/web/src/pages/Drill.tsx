import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState, type RefObject } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useOutletContext,
  useParams,
} from "react-router-dom";
import { ErrorBox, Loading } from "../components/ui";
import { api, ensureUser, queries, refreshLearning, userApi } from "../lib/api";
import { readLocal } from "../lib/drafts";
import { useUI } from "../lib/store";
import { keepPythonActive, warmPython } from "../features/python-runtime";
import { browserRun } from "../features/python";
import { readAnswer } from "../features/answer";
import { useDraft } from "../features/useDraft";
import { needsAnswer } from "../components/AnswerWorkspace";
import { DrillView } from "./DrillView";
import type {
  Attempt,
  Item,
  Job,
  Problem,
  Result,
  StudySession,
} from "../types/domain";

interface Loaded {
  item: Item & { problem: Problem };
  session: StudySession;
  code: string;
  revision: number;
  user: string;
  remoteCode: string | null;
  last: Attempt | null;
}
export function DrillPage() {
  useEffect(keepPythonActive, []);
  const { sessionId, itemId } = useParams();
  const { data, error, isPending } = useQuery({
    queryKey: ["workspace", sessionId, itemId],
    staleTime: 0,
    // A returning editor must mount with the saved draft, not a cached starter.
    gcTime: 0,
    refetchOnWindowFocus: false,
    queryFn: async () => {
      const user = await ensureUser();
      const [item, session, remote, local, last] = await Promise.all([
        api<Item & { problem: Problem }>(
          `/sessions/${sessionId}/items/${itemId}`,
        ),
        api<StudySession>(`/sessions/${sessionId}`),
        api<{ code: string | null; revision: number; updated_at?: string }>(
          `/drafts/${itemId}`,
        ),
        readLocal(user.id, itemId!),
        api<Attempt | null>(`/session-items/${itemId}/last-submission`),
      ]);
      const useLocal = local && local.dirty;
      return {
        item,
        session,
        last,
        code: useLocal
          ? local.code
          : (remote.code ?? local?.code ?? item.problem.starter_code),
        revision: useLocal ? local.revision : remote.revision,
        user: user.id,
        remoteCode: remote.code,
      } as Loaded;
    },
  });
  if (isPending) return <Loading />;
  if (error || !data) return <ErrorBox error={error} />;
  return <DrillWorkspace key={itemId} data={data} />;
}
function DrillWorkspace({ data }: { data: Loaded }) {
  const { item, session } = data,
    p = item.problem,
    navigate = useNavigate();
  const { data: dashboard } = useQuery(queries.dashboard);
  const location = useLocation();
  const { message: transition = "", focusAnswer = false } =
    (location.state as { message?: string; focusAnswer?: boolean } | null) ??
    {};
  const [notice, setNotice] = useState("");
  const [advancing, setAdvancing] = useState(false);
  const [nextReason, setNextReason] = useState("");
  const [ended, setEnded] = useState(false);
  const [editorRevision, refreshEditor] = useState(0);
  const [backup, setBackup] = useState<string | null>(null);
  const { code, setCode, status, save } = useDraft(
    data.user,
    item.id,
    data.code,
    data.revision,
    data.remoteCode,
  );
  const navigationSave =
    useOutletContext<RefObject<(() => Promise<void>) | null>>();
  useEffect(() => {
    navigationSave.current = save;
    return () => {
      navigationSave.current = null;
    };
  }, [navigationSave, save]);
  const { focus, setFocus, split, setSplit, resultHeight, setResultHeight } =
    useUI();
  const [leftTab, setLeftTab] = useState("problem"),
    [hints, setHints] = useState<string[]>([]),
    [hintLevel, setHintLevel] = useState(item.hint_level);
  const [solution, setSolution] = useState<{
    solution: string;
    explanation: string;
    common_mistakes: string[];
  } | null>(null);
  const [result, setResult] = useState<Result | null>(
      data.last
        ? {
            ...data.last.result,
            verification_level: data.last.verification_level,
          }
        : null,
    ),
    [resultCode, setResultCode] = useState(data.last?.submitted_code ?? ""),
    [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false),
    [phase, setPhase] = useState(""),
    [runCount, setRunCount] = useState(0),
    [submitted, setSubmitted] = useState(!!data.last);
  const [mobileTab, setMobileTab] = useState(
    focusAnswer ? "editor" : "problem",
  );
  const codeRef = useRef(code),
    abort = useRef<AbortController | null>(null),
    jobId = useRef<string | null>(null);
  const submitRequest = useRef<{ code: string; id: string } | null>(null),
    workspace = useRef<HTMLDivElement | null>(null),
    advancingRequest = useRef(false);
  codeRef.current = code;
  const stale = !!result && code !== resultCode;
  useEffect(() => () => abort.current?.abort(), []);
  useEffect(() => {
    if (p.runtime === "browser") warmPython();
  }, [p.runtime]);
  useEffect(() => {
    if (item.hint_level)
      void userApi<{ hints: string[] }>(
        `/session-items/${item.id}/hints/${item.hint_level}/reveal`,
        { method: "POST" },
      ).then((r) => setHints(r.hints));
  }, []);
  async function revealHint() {
    try {
      const res = await userApi<{ hints: string[]; level: number }>(
        `/session-items/${item.id}/hints/${Math.min(p.workspace?.hint_count ?? 3, Math.max(hintLevel, 2))}/reveal`,
        { method: "POST" },
      );
      setHints(res.hints);
      setHintLevel(res.level);
      setLeftTab("hints");
    } catch (e) {
      setError(e);
    }
  }
  async function revealSolution() {
    try {
      setSolution(
        await userApi(`/session-items/${item.id}/solution/reveal`, {
          method: "POST",
        }),
      );
      setLeftTab("solution");
    } catch (e) {
      setError(e);
    }
  }
  async function serverRun(
    captured: string,
    mode: "run" | "submit",
    signal: AbortSignal,
  ) {
    setPhase(
      mode === "submit"
        ? "非公開テストの正式検証を準備しています…"
        : "Sandboxを準備しています…",
    );
    const execution = await userApi<Job>("/executions", {
      method: "POST",
      body: JSON.stringify({
        item_id: item.id,
        code: captured,
        mode,
        client_request_id: crypto.randomUUID(),
      }),
      signal,
    });
    jobId.current = execution.id;
    let job = execution;
    const deadline = Date.now() + 300000;
    while (["queued", "running"].includes(job.status)) {
      if (signal.aborted) throw new DOMException("実行中止", "AbortError");
      if (Date.now() > deadline)
        throw new Error(
          "ジョブの待機上限を超えました。履歴から状態を確認してください。",
        );
      setPhase(
        job.status === "queued"
          ? "実行キューで待機中…"
          : "隔離Sandboxで検証中…",
      );
      await new Promise((r) => setTimeout(r, 800));
      job = await userApi<Job>(`/executions/${execution.id}`, { signal });
    }
    if (job.status === "cancelled")
      throw new DOMException("実行中止", "AbortError");
    if (!job.result) throw new Error("実行結果を取得できませんでした。");
    return { result: job.result, executionId: execution.id };
  }
  async function execute(submit = false) {
    if (busy || advancing || abort.current || advancingRequest.current) return;
    if (p.type !== "prediction" && needsAnswer(p, code)) {
      setNotice(
        "解答欄にコードを入力してください。入力データはそのまま使えます。",
      );
      setMobileTab("editor");
      return;
    }
    if (p.type === "prediction" && readAnswer(p, code) === "") {
      setNotice("予測した値を入力してください。");
      setMobileTab("editor");
      return;
    }
    setBusy(true);
    setPhase("");
    setError(null);
    setSubmitted(false);
    setResult(null);
    setNotice("");
    setMobileTab("editor");
    const captured = codeRef.current,
      controller = new AbortController();
    abort.current = controller;
    try {
      await save();
      if (controller.signal.aborted) return;
      let r: Result, executionId: string | undefined;
      const formal =
        submit &&
        (p.runtime === "sandbox" ||
          ((p.stage === "independent" ||
            p.required_ast.startsWith("comprehension:") ||
            p.required_ast.startsWith("all:") ||
            p.required_ast.startsWith("arguments:")) &&
            dashboard?.sandbox_available));
      if (p.runtime === "sandbox" || formal) {
        const res = await serverRun(
          captured,
          submit ? "submit" : "run",
          controller.signal,
        );
        r = res.result;
        executionId = res.executionId;
      } else {
        r = await browserRun(p, captured, setPhase, controller.signal);
      }
      if (controller.signal.aborted) return;
      setRunCount((v) => v + 1);
      if (codeRef.current !== captured) {
        setPhase("実行中にコードが変更されました。再実行してください。");
        setResult(r);
        setResultCode(captured);
        return;
      }
      setResult(r);
      setResultCode(captured);
      if (submit) {
        if (!submitRequest.current || submitRequest.current.code !== captured)
          submitRequest.current = { code: captured, id: crypto.randomUUID() };
        const attempt = await userApi<{
          result: Result;
          verification_level: string;
        }>("/submissions", {
          method: "POST",
          signal: controller.signal,
          body: JSON.stringify({
            item_id: item.id,
            code: captured,
            client_request_id: submitRequest.current.id,
            run_count: runCount + 1,
            ...(executionId
              ? { execution_id: executionId }
              : {
                  browser_result: {
                    verdict: r.verdict,
                    passed_tests: r.passed_tests,
                    total_tests: r.total_tests,
                    stdout: r.stdout ?? "",
                    stderr: r.stderr ?? "",
                    elapsed_ms: r.elapsed_ms ?? 0,
                    tests: r.tests?.map(
                      ({
                        name,
                        passed,
                        error,
                        actual,
                        actual_tuple_paths,
                      }) => ({
                        name,
                        passed,
                        error,
                        actual,
                        actual_tuple_paths,
                      }),
                    ),
                  },
                }),
          }),
        });
        if (controller.signal.aborted) return;
        setResult({ ...r, verification_level: attempt.verification_level });
        setSubmitted(true);
        submitRequest.current = null;
        await refreshLearning();
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError")
        setNotice("今回の実行を中止しました。回答は保持されています。");
      else setError(e);
    } finally {
      setBusy(false);
      abort.current = null;
      jobId.current = null;
    }
  }
  async function cancel() {
    abort.current?.abort();
    if (jobId.current)
      try {
        await userApi(`/executions/${jobId.current}/cancel`, {
          method: "POST",
        });
      } catch (e) {
        setError(e);
      }
  }
  async function next(skip = false, focusAnswer = false) {
    if (
      busy ||
      advancing ||
      abort.current ||
      advancingRequest.current ||
      (!skip && !(submitted && result?.verdict === "Accepted" && !stale))
    )
      return;
    advancingRequest.current = true;
    setAdvancing(true);
    setError(null);
    setNextReason("");
    try {
      await save();
      const response = await userApi<{
        session: StudySession;
        next_item_id: string | null;
        message: string;
        reason?: string;
      }>(`/sessions/${session.id}/advance`, {
        method: "POST",
        body: JSON.stringify({ from_item_id: item.id, skip }),
      });
      if (response.next_item_id)
        navigate(`/drill/s/${session.id}/${response.next_item_id}`, {
          state: { message: response.message, focusAnswer },
        });
      else
        setNextReason(
          response.reason ??
            "次の問題を取得できませんでした。別の演習を選べます。",
        );
      await refreshLearning();
    } catch (error) {
      setError(error);
    } finally {
      advancingRequest.current = false;
      setAdvancing(false);
    }
  }
  async function end() {
    if (busy || advancing) return;
    try {
      await save();
      await userApi(`/sessions/${session.id}/complete`, { method: "POST" });
      await refreshLearning();
      setEnded(true);
    } catch (error) {
      setError(error);
    }
  }
  async function pause() {
    try {
      if (busy) await cancel();
      await save();
      await userApi(`/sessions/${session.id}/pause?position=${item.position}`, {
        method: "POST",
      });
      await refreshLearning();
      navigate("/home");
    } catch (error) {
      setError(error);
    }
  }
  function resizeHorizontal(e: React.PointerEvent) {
    e.currentTarget.setPointerCapture(e.pointerId);
    const rect = workspace.current!.getBoundingClientRect();
    const move = (event: PointerEvent) =>
      setSplit(
        Math.min(
          60,
          Math.max(25, ((event.clientX - rect.left) / rect.width) * 100),
        ),
      );
    const end = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", end);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", end);
  }
  function resizeVertical(e: React.PointerEvent) {
    const startY = e.clientY,
      startH = resultHeight;
    const move = (event: PointerEvent) =>
      setResultHeight(
        Math.max(140, Math.min(500, startH + startY - event.clientY)),
      );
    const end = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", end);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", end);
  }
  if (ended)
    return (
      <section className="drill-ended">
        <h1>今回の演習を終了しました</h1>
        <p>提出した解答は履歴に残っています。途中の回答も保存しました。</p>
        <Link className="btn primary" to="/history">
          解答履歴を見る
        </Link>
        <Link className="btn secondary" to="/drill">
          新しい演習を始める
        </Link>
      </section>
    );
  const canNext =
    !!result && result.verdict === "Accepted" && submitted && !stale;
  return (
    <DrillView
      p={p}
      item={item}
      session={session}
      code={code}
      editorRevision={editorRevision}
      status={status}
      result={result}
      stale={stale}
      submitted={submitted}
      busy={busy}
      phase={phase}
      notice={notice}
      error={error}
      advancing={advancing}
      nextReason={nextReason}
      transition={transition}
      hints={hints}
      hintLevel={hintLevel}
      solution={solution}
      leftTab={leftTab}
      mobileTab={mobileTab}
      focusAnswer={focusAnswer}
      focus={focus}
      split={split}
      resultHeight={resultHeight}
      workspace={workspace}
      canNext={canNext}
      restored={backup !== null}
      sandboxAvailable={dashboard?.sandbox_available ?? false}
      fontSize={dashboard?.settings.font_size}
      theme={dashboard?.settings.theme}
      actions={{
        check: () => void execute(true),
        run: () => void execute(),
        next: (focusAnswer) => void next(false, focusAnswer),
        skip: () => void next(true),
        cancel: () => void cancel(),
        pause: () => void pause(),
        end: () => void end(),
        hint: () => void revealHint(),
        solution: () => void revealSolution(),
        restore: () => {
          setBackup(code);
          setCode(p.starter_code);
          refreshEditor((n) => n + 1);
        },
        undo: () => {
          if (backup !== null) {
            setCode(backup);
            refreshEditor((n) => n + 1);
          }
          setBackup(null);
        },
        code: setCode,
        mobile: setMobileTab,
        tab: setLeftTab,
        focus: () => setFocus(!focus),
        resizeH: resizeHorizontal,
        resizeV: resizeVertical,
      }}
    />
  );
}
