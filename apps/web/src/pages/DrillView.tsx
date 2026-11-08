import {
  useEffect,
  useEffectEvent,
  useRef,
  type PointerEvent,
  type RefObject,
} from "react";
import { Link } from "react-router-dom";
import { Button, ErrorBox, typeLabels } from "../components/ui";
import { AnswerWorkspace, needsAnswer } from "../components/AnswerWorkspace";
import { ResultValue } from "../components/ResultValue";
import { ComputedResult, hasActualValue } from "../components/ComputedResult";
import {
  signature,
  answerCode,
  readAnswer,
  taskText,
  outputDescription,
} from "../features/answer";
import type { Item, Problem, Result, StudySession } from "../types/domain";
import "./Drill.css";

interface Props {
  p: Problem;
  item: Item;
  session: StudySession;
  code: string;
  editorRevision: number;
  status: string;
  result: Result | null;
  stale: boolean;
  submitted: boolean;
  busy: boolean;
  phase: string;
  notice: string;
  error: unknown;
  advancing: boolean;
  nextReason: string;
  transition: string;
  hints: string[];
  hintLevel: number;
  solution: {
    solution: string;
    explanation: string;
    common_mistakes: string[];
  } | null;
  leftTab: string;
  mobileTab: string;
  focusAnswer: boolean;
  focus: boolean;
  split: number;
  resultHeight: number;
  workspace: RefObject<HTMLDivElement | null>;
  canNext: boolean;
  restored: boolean;
  sandboxAvailable: boolean;
  fontSize?: number;
  theme?: string;
  actions: {
    check: () => void;
    run: () => void;
    next: (focusAnswer?: boolean) => void;
    skip: () => void;
    cancel: () => void;
    pause: () => void;
    end: () => void;
    hint: () => void;
    solution: () => void;
    restore: () => void;
    undo: () => void;
    code: (v: string) => void;
    mobile: (v: string) => void;
    tab: (v: string) => void;
    focus: () => void;
    resizeH: (e: PointerEvent) => void;
    resizeV: (e: PointerEvent) => void;
  };
}
const libraries: Record<string, string> = {
  python: "Python",
  numpy: "NumPy",
  pandas: "Pandas",
  sklearn: "scikit-learn",
  pytorch: "PyTorch",
};
const verdicts: Record<string, string> = {
  Accepted: "正解です",
  "Wrong Answer": "結果が異なります",
  "Runtime Error": "実行中にエラーがありました",
  "Syntax Error": "コードの書き方を確認してください",
  "Time Limit Exceeded": "実行時間の上限を超えました",
};

function inlineCode(text: string) {
  return text
    .split(/(`[^`\n]+`)/)
    .map((part, i) =>
      part.startsWith("`") && part.endsWith("`") ? (
        <code key={i}>{part.slice(1, -1)}</code>
      ) : (
        part
      ),
    );
}

function shortcutAction(event: KeyboardEvent, mac: boolean) {
  if (event.getModifierState("AltGraph")) return;
  if (event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    // Option can produce a symbol instead of the letter in KeyboardEvent.key.
    const key = /^[a-z]$/i.test(event.key)
      ? event.key.toLowerCase()
      : event.code;
    if (key === "h" || key === "KeyH") return "hint";
    if (key === "j" || key === "KeyJ") return "solution";
    if (key === "n" || key === "KeyN") return "next"; // Existing Drill alias.
  }
  if (
    event.key === "Enter" &&
    (mac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey)
  ) {
    if (event.altKey) return event.shiftKey ? undefined : "run";
    return event.shiftKey ? "next" : "submit";
  }
}

export function DrillView(v: Props) {
  const { p, item, session, result, actions: a } = v;
  const prediction = p.type === "prediction";
  const answer = prediction ? readAnswer(p, v.code) : null;
  const unavailable = p.runtime === "sandbox" && !v.sandboxAvailable;
  const accepted = result?.verdict === "Accepted";
  const mac = /Mac|iPhone|iPad|iPod/i.test(navigator.platform);
  const alt = mac ? "Option" : "Alt";
  const command = mac ? "Cmd" : "Ctrl";
  const ariaCommand = mac ? "Meta" : "Control";
  const primaryLabel = v.advancing
    ? "次の問題を準備中…"
    : v.canNext
      ? "次の問題"
      : result && !v.stale && !accepted
        ? "もう一度答え合わせ"
        : "答え合わせ";
  const primaryDisabled = v.busy || v.advancing || (!v.canNext && unavailable);
  const root = useRef<HTMLDivElement>(null);
  const hint = useRef<HTMLElement>(null);
  const solution = useRef<HTMLElement>(null);
  const predictionInput = useRef<HTMLTextAreaElement>(null);
  const answerFocus = useRef<(() => void) | null>(null);
  const composing = useRef(false);
  const returnToAnswer = useRef(false);

  const onShortcut = useEffectEvent((event: KeyboardEvent) => {
    if (
      event.defaultPrevented ||
      event.isComposing ||
      event.keyCode === 229 ||
      composing.current ||
      (event.target !== document.body &&
        !(event.target instanceof Node && root.current?.contains(event.target)))
    )
      return;
    const action = shortcutAction(event, mac);
    if (!action || document.querySelector("dialog:modal")) return;

    // These combinations belong to Drill even while its action is disabled.
    // In particular, do not let Monaco insert a line on a premature advance.
    event.preventDefault();
    event.stopPropagation();
    if (event.repeat) return;

    if (action === "hint" || action === "solution") {
      const summary = (action === "hint" ? hint : solution).current;
      if (!summary) return;
      summary.click();
      if (matchMedia("(max-width: 1023px)").matches) {
        if (summary.parentElement?.hasAttribute("open")) {
          returnToAnswer.current ||= v.mobileTab === "editor";
          a.mobile("problem");
        } else if (
          returnToAnswer.current &&
          !hint.current?.parentElement?.hasAttribute("open") &&
          !solution.current?.parentElement?.hasAttribute("open")
        ) {
          returnToAnswer.current = false;
          a.mobile("editor");
          requestAnimationFrame(() => {
            predictionInput.current?.focus();
            answerFocus.current?.();
          });
        }
      }
    } else if (!primaryDisabled) {
      if (action === "next" && v.canNext) a.next(true);
      if (
        (action === "submit" || action === "run") &&
        !v.canNext &&
        (prediction ? answer !== "" : !needsAnswer(p, v.code))
      )
        (action === "submit" ? a.check : a.run)();
    }
  });
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => onShortcut(event);
    window.addEventListener("keydown", keydown, true);
    return () => window.removeEventListener("keydown", keydown, true);
  }, []);
  useEffect(() => {
    if (v.focusAnswer) predictionInput.current?.focus();
  }, [v.focusAnswer]);

  const emptyResult =
    !result &&
    !v.busy &&
    !v.error &&
    !v.notice &&
    !v.nextReason &&
    !unavailable;
  return (
    <div
      className="drill-workspace phase-one"
      ref={root}
      onCompositionStartCapture={() => {
        composing.current = true;
      }}
      onCompositionEndCapture={() => {
        composing.current = false;
      }}
    >
      <header className="drill-top">
        <span className="session-label">
          {libraries[p.module_id]} /{" "}
          {p.type === "completion"
            ? p.stage === "guided"
              ? "穴埋め"
              : "部分記述"
            : typeLabels[p.type]}
        </span>
        <span className="drill-count">
          {item.position + 1}問目{" "}
          <small>目安 {session.goal_count ?? 20}問</small>
        </span>
        <details className="drill-menu">
          <summary>演習メニュー</summary>
          <div>
            <button onClick={a.pause} disabled={v.busy || v.advancing}>
              中断して保存
            </button>
            <button onClick={a.end} disabled={v.busy || v.advancing}>
              演習を終了
            </button>
            <button onClick={a.skip} disabled={v.busy || v.advancing}>
              この問題は後で
            </button>
            <Link to="/drill">別の演習を選ぶ</Link>
          </div>
        </details>
      </header>
      {v.transition && (
        <p className="transition-note" role="status">
          {v.transition}
        </p>
      )}
      <div className="drill-mobile-tabs" role="tablist" aria-label="演習の表示">
        <button
          role="tab"
          aria-selected={v.mobileTab === "problem"}
          className={v.mobileTab === "problem" ? "active" : ""}
          onClick={() => a.mobile("problem")}
        >
          問題
        </button>
        <button
          role="tab"
          aria-selected={v.mobileTab === "editor"}
          className={v.mobileTab === "editor" ? "active" : ""}
          onClick={() => a.mobile("editor")}
        >
          回答・結果
        </button>
      </div>
      <div
        className="drill-panes"
        ref={v.workspace}
        style={
          {
            "--left-width": `${v.split}%`,
            "--result-height": `${v.resultHeight}px`,
          } as React.CSSProperties
        }
      >
        <section
          className={`problem-pane ${v.mobileTab === "problem" ? "mobile-active" : ""}`}
          aria-label="問題"
        >
          <div className="problem-content">
            <h1>{p.title}</h1>
            <p className="problem-description">
              {p.workspace?.hint_count === 1
                ? inlineCode(taskText(p))
                : taskText(p)}
            </p>
            {prediction && (
              <pre className="prediction-observation">
                {p.workspace?.provided_code ?? p.example}
              </pre>
            )}
            <button
              className="mobile-answer-link"
              onClick={() => a.mobile("editor")}
            >
              回答欄へ
            </button>
            {unavailable && (
              <div className="runtime-unavailable" role="status">
                この環境では、この問題を実行できません。コードやヒントは読めます。
                <Link to="/curriculum/numpy">NumPyの演習を選ぶ</Link>
              </div>
            )}
            <details
              className="drill-hints"
              onToggle={(e) => {
                if (
                  e.currentTarget.open &&
                  v.hintLevel < Math.min(2, p.workspace?.hint_count ?? 3)
                )
                  a.hint();
              }}
            >
              <summary ref={hint} aria-keyshortcuts="Alt+H">
                ヒント
                <kbd className="drill-shortcut" aria-hidden="true">
                  {alt} + H
                </kbd>
              </summary>
              {v.hints.length ? (
                <p>
                  {p.workspace?.hint_count === 1
                    ? inlineCode(v.hints[0])
                    : v.hints[Math.min(1, v.hints.length - 1)]}
                </p>
              ) : (
                <p>読み込み中…</p>
              )}
            </details>
            <details
              className="solution-accordion"
              onToggle={(e) => {
                if (e.currentTarget.open && !v.solution) a.solution();
              }}
            >
              <summary ref={solution} aria-keyshortcuts="Alt+J">
                模範解答
                <kbd className="drill-shortcut" aria-hidden="true">
                  {alt} + J
                </kbd>
              </summary>
              {v.solution ? (
                prediction ? (
                  <ResultValue
                    value={p.public_tests[0]?.expected}
                    tuplePaths={p.public_tests[0]?.expected_tuple_paths}
                    checkDtype={p.check_dtype}
                  />
                ) : (
                  <pre>{v.solution.solution}</pre>
                )
              ) : (
                <p>読み込み中…</p>
              )}
            </details>
          </div>
        </section>
        <div
          className="resize-handle horizontal"
          onPointerDown={a.resizeH}
          role="separator"
          aria-label="問題と回答の幅を調整"
        />
        <section
          className={`editor-pane ${v.mobileTab === "editor" ? "mobile-active" : ""}`}
          aria-label="回答"
        >
          <div className="editor-heading">
            <span>{prediction ? "回答値" : "solution.py"}</span>
            <span
              className={`save-status ${v.status.includes("競合") ? "warning" : ""}`}
            >
              {v.status}
            </span>
            <details className="drill-menu">
              <summary>回答の操作</summary>
              <div>
                <button onClick={a.restore} disabled={v.busy}>
                  初期状態に戻す
                </button>
              </div>
            </details>
          </div>

          <details className="mobile-contract">
            <summary>問題を見ながら考える</summary>
            <strong>{p.title}</strong>
            <p>
              {p.workspace?.hint_count === 1
                ? inlineCode(taskText(p))
                : taskText(p)}
            </p>
            {!p.editable_regions?.length && <p>{outputDescription(p)}</p>}
            {prediction && p.workspace && (
              <pre>{p.workspace.provided_code}</pre>
            )}
          </details>
          {v.restored && (
            <p className="restore-notice" role="status">
              初期状態に戻しました。
              <button onClick={a.undo}>変更前の回答を戻す</button>
            </p>
          )}
          <div
            className={`editor-area ${prediction && answer !== null ? "prediction-area" : ""}`}
          >
            {prediction && answer !== null ? (
              <div className="prediction-answer">
                <label htmlFor="prediction-value">
                  {p.presentation?.answer?.mode === "fixed"
                    ? "observedに入る値"
                    : "戻り値（数値・shape・Pythonの式）"}
                </label>
                <textarea
                  id="prediction-value"
                  ref={predictionInput}
                  spellCheck={false}
                  value={answer}
                  onChange={(e) => a.code(answerCode(p, e.target.value))}
                  placeholder={
                    p.presentation?.answer?.wrap_array
                      ? "例: [[1, 2], [3, 4]]"
                      : "例: 3、(2, 3)、{'key': [1, 2]}"
                  }
                />
                <p>
                  関数の定義やreturnは不要です。
                  {p.presentation?.answer?.mode !== "fixed" &&
                    "入力で値が変わる場合は、引数名を使った式で答えます。"}
                </p>
                {p.presentation?.answer?.mode !== "fixed" && (
                  <code>
                    使える引数:{" "}
                    {signature(p)
                      .replace(/^def solve\(/, "")
                      .replace(/\):$/, "")}
                  </code>
                )}
              </div>
            ) : (
              <>
                <AnswerWorkspace
                  key={v.editorRevision}
                  p={p}
                  code={v.code}
                  onChange={a.code}
                  fontSize={v.fontSize ?? 15}
                  theme={v.theme}
                  errorLine={result?.error_line}
                  autoFocus={v.focusAnswer}
                  onFocusReady={(focus) => {
                    answerFocus.current = focus;
                  }}
                  onCompositionChange={(active) => {
                    composing.current = active;
                  }}
                />
                {prediction && (
                  <p className="legacy-answer-note">
                    保存済みのコードを読み込んでいます。現在の回答を保持してコードで答え合わせできます。
                  </p>
                )}
              </>
            )}
          </div>
          <div
            className={`resize-handle vertical ${emptyResult ? "unused-result" : ""}`}
            onPointerDown={a.resizeV}
            role="separator"
            aria-label="回答と結果の高さを調整"
          />
          <section
            className={`results-panel ${result && !accepted ? "has-mismatch" : ""} ${emptyResult ? "unused-result" : ""}`}
            aria-label="答え合わせの結果"
          >
            <div className="result-content" aria-live="polite">
              {v.error ? (
                <ErrorBox error={v.error} />
              ) : v.busy ? (
                <div className="runtime-loading">
                  <p>{v.phase || "答えを確認しています…"}</p>
                </div>
              ) : result ? (
                <>
                  {v.stale && (
                    <p className="stale-notice">
                      回答が変更されました。表示は変更前の結果です。もう一度答え合わせしてください。
                    </p>
                  )}
                  <div
                    className={`verdict ${accepted ? "accepted" : "failed"}`}
                  >
                    <strong>
                      {verdicts[result.verdict] ?? result.verdict}
                    </strong>
                    <span>
                      {result.passed_tests}/{result.total_tests}件
                    </span>
                  </div>
                  <ComputedResult result={result} />
                  {!accepted && (
                    <p className="answer-guidance">
                      {result.verdict === "Wrong Answer"
                        ? (p.presentation?.feedback.wrong ??
                          "入力・返す値の形・条件を確認し、下の動作確認で違いを比べてください。")
                        : (p.presentation?.feedback.runtime ??
                          "エラーの種類と、示された行を確認してください。")}
                    </p>
                  )}
                  {result.error_line && !accepted && (
                    <p>解答部分の{result.error_line}行目を確認してください。</p>
                  )}
                  {result.stderr && (
                    <pre className="stderr">{result.stderr}</pre>
                  )}
                  <details className="checks">
                    <summary>動作確認</summary>
                    {p.public_tests.map((t, i) => {
                      const observed = result.tests?.[i];
                      return (
                        <div className="case-result" key={i}>
                          <p>
                            入力例 {i + 1}
                            {observed
                              ? observed.passed
                                ? " · 一致"
                                : " · 要確認"
                              : ""}
                          </p>
                          <code>
                            {p.execution?.mode === "script"
                              ? `入力: ${t.args}`
                              : `${p.execution?.entrypoint ?? "solve"}(${t.args})`}
                          </code>
                          <div className="value-comparison">
                            <div>
                              <h4>期待する値</h4>
                              <ResultValue
                                value={t.expected}
                                tuplePaths={t.expected_tuple_paths}
                                checkDtype={p.check_dtype}
                              />
                            </div>
                            <div>
                              <h4>あなたの値</h4>
                              {hasActualValue(observed, result.verdict) ? (
                                <>
                                  <ResultValue
                                    value={observed.actual}
                                    tuplePaths={observed.actual_tuple_paths}
                                    warnMissingTupleTypes
                                    checkDtype={p.check_dtype}
                                  />
                                  {observed.error && <p>{observed.error}</p>}
                                </>
                              ) : (
                                <p>
                                  {observed?.error ??
                                    "この保存結果には値の詳細がありません。実行し直すと確認できます。"}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </details>
                  {result.stdout && (
                    <details>
                      <summary>出力（print）</summary>
                      <pre className="console-output">{result.stdout}</pre>
                    </details>
                  )}
                </>
              ) : (
                <p className="result-empty">
                  {unavailable
                    ? "この環境では実行できません。問題やヒントを読むか、別の演習を選べます。"
                    : prediction
                      ? "予測した値を入力して、答え合わせしましょう。"
                      : "コードを書いたら、答え合わせしましょう。"}
                </p>
              )}
              {v.notice && (
                <p role="status" className="execution-notice">
                  {v.notice}
                </p>
              )}
              {v.nextReason && (
                <div className="no-next" role="status">
                  <p>{v.nextReason}</p>
                  <Link to="/drill">演習の条件を変える</Link>
                  <Link to="/curriculum">別の概念を選ぶ</Link>
                </div>
              )}
            </div>
          </section>
          <footer className="editor-footer">
            <div>
              {v.busy ? (
                <Button variant="secondary" onClick={a.cancel}>
                  中止
                </Button>
              ) : (
                <>
                  {!v.canNext && (
                    <button
                      className="text-action run-only"
                      onClick={a.run}
                      disabled={(!v.canNext && unavailable) || v.advancing}
                    >
                      実行のみ
                    </button>
                  )}
                  <Button
                    onClick={() => (v.canNext ? a.next() : a.check())}
                    disabled={primaryDisabled}
                    aria-label={primaryLabel}
                    aria-keyshortcuts={`${ariaCommand}+${v.canNext ? "Shift+" : ""}Enter`}
                  >
                    {primaryLabel}
                    <kbd className="drill-shortcut" aria-hidden="true">
                      {command} + {v.canNext ? "Shift + " : ""}Enter
                    </kbd>
                  </Button>
                </>
              )}
            </div>
          </footer>
        </section>
      </div>
    </div>
  );
}
