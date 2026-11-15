import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronRight, Search } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import {
  newSession,
  practiceCount,
  problemCount,
  queries,
  queryClient,
  refreshLearning,
  sessionPath,
} from "../lib/api";
import { Badge, ErrorBox, Loading, PageTitle } from "../components/ui";
export function Curriculum() {
  const { moduleId } = useParams(),
    [search, setSearch] = useState("");
  const {
      data: modules = [],
      isPending: loadingModules,
      error: moduleError,
    } = useQuery(queries.modules),
    { data: concepts = [], isPending, error } = useQuery(queries.concepts),
    { data: d } = useQuery(queries.dashboard);
  const module = modules.find((m) => m.id === moduleId);
  const listed = moduleId
    ? concepts.filter((c) => c.module_id === moduleId)
    : concepts;
  if (isPending || loadingModules) return <Loading />;
  if (error || moduleError) return <ErrorBox error={error ?? moduleError} />;
  return (
    <>
      <PageTitle
        eyebrow="CURRICULUM"
        title={module?.title ?? "学習カリキュラム"}
        description={
          module?.subtitle ??
          "PythonやSQLで、データサイエンスに使うコードを1問ずつ練習できます。"
        }
      >
        <Badge color="green">{problemCount(listed)}問のDrill</Badge>
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
                {concepts.filter((c) => c.module_id === m.id).length}概念
                {m.id === "sql" && " · ブラウザ採点（暫定）"}
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
                          {c.mastery_available === false
                            ? `練習 ${practiceCount([c], d)}/${c.problem_count}問正解`
                            : p
                              ? `習熟度 ${p.mastery_level}/5`
                              : "未測定"}
                        </Badge>
                      </div>
                      <h3>{c.title}</h3>
                      <p>{c.description}</p>
                      <pre className="code-preview">{c.example}</pre>
                      <div className="concept-card-bottom">
                        <span>{c.problem_count}問</span>
                        <span>
                          演習を始める
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
// Concepts have no page of their own: opening one resumes its active session,
// or starts a new one, and goes straight to the current problem.
export function ConceptStart() {
  const { conceptId = "" } = useParams(),
    navigate = useNavigate(),
    started = useRef(false),
    [err, setErr] = useState<unknown>(null);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    (async () => {
      const dashboard = await queryClient.fetchQuery({
        ...queries.dashboard,
        staleTime: 0,
      });
      const current = dashboard.current_session;
      if (current?.kind === "concept" && current.concept_id === conceptId) {
        navigate(sessionPath(current), { replace: true });
        return;
      }
      const session = await newSession({
        kind: "concept",
        concept_id: conceptId,
      });
      await refreshLearning();
      navigate(sessionPath(session), { replace: true });
    })().catch(setErr);
  }, [conceptId, navigate]);
  if (!err) return <Loading />;
  return (
    <>
      <Link className="back-link" to="/curriculum">
        <ArrowLeft size={15} />
        カリキュラムに戻る
      </Link>
      <ErrorBox error={err} />
    </>
  );
}
