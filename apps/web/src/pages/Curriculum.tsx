import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Circle,
  Play,
  Search,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import {
  api,
  newSession,
  problemCount,
  queries,
  sessionPath,
} from "../lib/api";
import {
  Badge,
  Button,
  ErrorBox,
  Loading,
  PageTitle,
  ProgressBar,
  stageLabels,
  typeLabels,
} from "../components/ui";
import type { Concept, Stage } from "../types/domain";
export function Curriculum() {
  const { moduleId } = useParams(),
    [search, setSearch] = useState("");
  const { data: modules = [] } = useQuery(queries.modules),
    { data: concepts = [], isPending, error } = useQuery(queries.concepts),
    { data: d } = useQuery(queries.dashboard);
  const module = modules.find((m) => m.id === moduleId);
  if (isPending) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  return (
    <>
      <PageTitle
        eyebrow="LEARNING PATH"
        title={module?.title ?? "学習カリキュラム"}
        description={
          module?.subtitle ??
          "5つの分野、30の概念。小さな実装から、読めるコードを増やしていく。"
        }
      >
        <Badge color="green">{problemCount(concepts)}問のDrill</Badge>
      </PageTitle>
      <div className="curriculum-toolbar">
        <div className="filter-tabs">
          <Link className={!moduleId ? "selected" : ""} to="/curriculum">
            すべて
          </Link>
          {modules.map((m) => (
            <Link
              className={m.id === moduleId ? "selected" : ""}
              to={`/curriculum/${m.id}`}
              key={m.id}
            >
              {m.title}
            </Link>
          ))}
        </div>
        <label className="search-box">
          <Search size={16} />
          <input
            placeholder="概念を検索"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>
      {modules
        .filter((m) => !moduleId || m.id === moduleId)
        .map((m) => (
          <section className="curriculum-module" key={m.id}>
            <div className="curriculum-module-heading">
              <div>
                <span className="eyebrow" style={{ color: m.color }}>
                  {m.id.toUpperCase()}
                </span>
                <h2>{m.title}</h2>
                <p>{m.subtitle}</p>
              </div>
              <span className="muted">
                {concepts.filter((c) => c.module_id === m.id).length}概念 ·
                3ステージ
              </span>
            </div>
            <div className="concept-grid">
              {concepts
                .filter(
                  (c) =>
                    c.module_id === m.id &&
                    `${c.id}${c.title}`
                      .toLowerCase()
                      .includes(search.toLowerCase()),
                )
                .map((c) => {
                  const p = d?.concepts.find((p) => p.concept_id === c.id);
                  return (
                    <Link
                      className="concept-card panel"
                      key={c.id}
                      to={`/concepts/${c.id}`}
                    >
                      <div className="concept-card-top">
                        <span className="mono muted">{c.id}</span>
                        <Badge color={p ? "green" : "gray"}>
                          {p ? `習熟度 ${p.mastery_level}/5` : "未測定"}
                        </Badge>
                      </div>
                      <h3>{c.title}</h3>
                      <p>{c.description}</p>
                      <pre className="code-preview">{c.example}</pre>
                      <div className="stage-dots">
                        {(["guided", "partial", "independent"] as Stage[]).map(
                          (s) => (
                            <span key={s}>
                              {(p?.stage_families[s]?.length ?? 0) >= 2 ? (
                                <CheckCircle2 size={13} />
                              ) : (
                                <Circle size={13} />
                              )}{" "}
                              {stageLabels[s]}
                            </span>
                          ),
                        )}
                      </div>
                      <div className="concept-card-bottom">
                        <span>
                          {c.problem_count
                            ? `${c.problem_count}問`
                            : "6問 · 約12分"}
                        </span>
                        <span>
                          概念を学ぶ
                          <ChevronRight size={14} />
                        </span>
                      </div>
                    </Link>
                  );
                })}
            </div>
          </section>
        ))}
      {!concepts.some(
        (c) =>
          (!moduleId || c.module_id === moduleId) &&
          `${c.id}${c.title}`.toLowerCase().includes(search.toLowerCase()),
      ) && <div className="empty">該当する概念がありません。</div>}
    </>
  );
}
export function ConceptDetail() {
  const { conceptId } = useParams(),
    navigate = useNavigate(),
    [err, setErr] = useState<unknown>(null),
    [busy, setBusy] = useState(false);
  const {
    data: c,
    isPending,
    error,
  } = useQuery({
    queryKey: ["concept", conceptId],
    queryFn: () => api<Concept>(`/concepts/${conceptId}`),
  });
  const { data: d } = useQuery(queries.dashboard);
  if (isPending) return <Loading />;
  if (error || !c) return <ErrorBox error={error} />;
  const p = d?.concepts.find((p) => p.concept_id === c.id);
  const exerciseCount = c.problem_count ?? 6;
  const orderedProblems = c.ordered_practice ? c.problems : undefined;
  const includesFunctionDefinitions = orderedProblems?.some(
    (problem) => problem.workspace?.structure === "function",
  );
  async function start(stage?: Stage) {
    setBusy(true);
    try {
      navigate(
        sessionPath(
          await newSession({
            kind: "concept",
            concept_id: conceptId,
            count:
              stage && orderedProblems
                ? orderedProblems.filter((item) => item.stage === stage).length
                : exerciseCount,
            ...(stage ? { stages: [stage] } : {}),
          }),
        ),
      );
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Link className="back-link" to={`/curriculum/${c.module_id}`}>
        <ArrowLeft size={15} />
        カリキュラムに戻る
      </Link>
      <PageTitle
        eyebrow={`${c.id} / CONCEPT`}
        title={c.title}
        description={c.description}
      >
        <Button disabled={busy} onClick={() => start()}>
          <Play size={16} />
          演習を開始
          <ArrowRight size={17} />
        </Button>
      </PageTitle>
      {!!err && <ErrorBox error={err} />}
      <div className="concept-detail-grid">
        <section className="panel info-panel">
          <h2>コードの読みどころ</h2>
          <p>{c.description}</p>
          <pre>{c.example}</pre>
          <h3>前提知識</h3>
          <div className="tag-row">
            {c.prerequisites.length ? (
              c.prerequisites.map((id) => (
                <Link to={`/concepts/${id}`} key={id}>
                  <Badge>{id}</Badge>
                </Link>
              ))
            ) : (
              <Badge color="gray">Pythonの基本構文</Badge>
            )}
          </div>
          <h3>現在の習熟度</h3>
          <strong>{p ? `${p.mastery_level} / 5` : "未測定"}</strong>
          <ProgressBar value={(p?.mastery_level ?? 0) * 20} />
          <p className="muted">
            Guided・Partialは暫定進捗です。自力実装の習得認定にはサーバー検証が必要です。
          </p>
        </section>
        <section>
          <h2 className="mb-20">3ステージで身につける</h2>
          {(["guided", "partial", "independent"] as Stage[]).map((stage, i) => (
            <div className="stage-card panel" key={stage}>
              <div className="stage-number">0{i + 1}</div>
              <div>
                <h3>
                  {stageLabels[stage]}
                  <Badge color="gray">
                    {p?.stage_families[stage]?.length ?? 0}/2
                  </Badge>
                </h3>
                <p>
                  {c.ordered_practice
                    ? includesFunctionDefinitions
                      ? "指定の順番で、関数の呼び出しや定義を書く"
                      : "指定の順番で、式全体を書いて練習する"
                    : [
                        "完成に近いコードの空欄を埋める",
                        "APIや引数を選び、部分的に実装する",
                        "最小限の条件から、自力で実装する",
                      ][i]}
                </p>
                <ul>
                  {c.problems
                    ?.filter((p) => p.stage === stage)
                    .map((p) => (
                      <li key={p.id}>
                        <span>{p.title}</span>
                        <small>{typeLabels[p.type]}</small>
                      </li>
                    ))}
                </ul>
                <Button
                  variant="secondary"
                  onClick={() => start(stage)}
                  disabled={busy}
                >
                  このステージを練習
                  <ChevronRight size={15} />
                </Button>
              </div>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}
