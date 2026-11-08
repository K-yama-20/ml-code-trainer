import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Code2,
  Flame,
} from "lucide-react";
import { Link } from "react-router-dom";
import { queries, userApi } from "../lib/api";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  PageTitle,
  ProgressBar,
  SectionTitle,
  typeLabels,
} from "../components/ui";
import { useState } from "react";
import type { Attempt } from "../types/domain";
export function Analytics() {
  const { data: d, error, isPending } = useQuery(queries.dashboard),
    { data: concepts = [] } = useQuery(queries.concepts),
    { data: modules = [] } = useQuery(queries.modules);
  if (isPending) return <Loading />;
  if (error || !d) return <ErrorBox error={error} />;
  const weak = d.concepts
    .filter((p) => p.mastery_level < 3)
    .sort((a, b) => a.mastery_score - b.mastery_score)
    .slice(0, 4);
  return (
    <>
      <PageTitle
        eyebrow="LEARNING INSIGHTS"
        title="積み重ねを、見える形に。"
        description="できることと、これからできること。学習の現在地を確かめましょう。"
      />
      <div className="analytics-stats">
        {[
          {
            label: "累計解答数",
            value: d.total_attempts,
            unit: "問",
            icon: Code2,
          },
          {
            label: "学習日数",
            value: d.study_days,
            unit: "日",
            icon: CalendarDays,
          },
          { label: "連続学習", value: d.streak, unit: "日", icon: Flame },
          {
            label: "習得済み概念",
            value: d.mastered,
            unit: "/30",
            icon: CheckCircle2,
          },
        ].map(({ icon: Icon, ...x }) => (
          <div className="stat-card" key={x.label}>
            <div className="stat-top">
              {x.label}
              <Icon size={18} />
            </div>
            <div className="stat-value">
              {x.value}
              <span>{x.unit}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="analytics-grid">
        <section className="panel info-panel">
          <SectionTitle title="ライブラリ別の習熟度" />
          {modules.map((m) => {
            const cs = concepts.filter((c) => c.module_id === m.id),
              ps = d.concepts.filter((p) =>
                cs.some((c) => c.id === p.concept_id),
              );
            return (
              <div className="mastery-row" key={m.id}>
                <div>
                  <strong>{m.title}</strong>
                  <span>
                    {ps.length
                      ? `${Math.round((ps.reduce((s, p) => s + p.mastery_score, 0) / cs.length) * 100)}%`
                      : "未測定"}
                  </span>
                </div>
                <ProgressBar
                  value={
                    (ps.reduce((s, p) => s + p.mastery_score, 0) / cs.length) *
                    100
                  }
                  color={m.color}
                />
                <small>
                  {ps.length}/{cs.length}概念を学習
                </small>
              </div>
            );
          })}
          <p className="small-copy muted">
            未測定は提出がまだない状態です。正式な自力実装の認定にはサーバー検証を使います。
          </p>
        </section>
        <section className="panel info-panel">
          <SectionTitle title="能力別の進捗" />
          {Object.entries(d.abilities).map(([type, a]) => (
            <div className="mastery-row" key={type}>
              <div>
                <strong>{typeLabels[type]}</strong>
                <span>
                  {a.attempts ? `${a.accepted}/${a.attempts} 正解` : "未測定"}
                </span>
              </div>
              <ProgressBar
                value={(a.accepted / Math.max(1, a.attempts)) * 100}
              />
            </div>
          ))}
          <h3 className="mt-32">この7日間の解答数</h3>
          <div className="analytics-week">
            {d.weekly.map((x) => (
              <div key={x.date}>
                <span>{x.count}</span>
                <div
                  style={{
                    height: `${Math.max(3, (x.count / Math.max(1, ...d.weekly.map((x) => x.count))) * 90)}px`,
                  }}
                />
                <small>
                  {new Date(x.date + "T12:00:00").toLocaleDateString("ja-JP", {
                    weekday: "short",
                  })}
                </small>
              </div>
            ))}
          </div>
        </section>
      </div>
      <div className="analytics-grid">
        <section className="panel info-panel">
          <SectionTitle title="復習の予定" to="/drill" label="復習する" />
          {d.reviews.length ? (
            d.reviews.slice(0, 8).map((r) => (
              <div className="review-row" key={r.concept_id}>
                <CalendarDays size={18} />
                <div>
                  <Link to={`/concepts/${r.concept_id}`}>
                    {concepts.find((c) => c.id === r.concept_id)?.title}
                  </Link>
                  <small>間隔 {r.interval_days}日</small>
                </div>
                <Badge
                  color={new Date(r.due_at) < new Date() ? "amber" : "gray"}
                >
                  {new Date(r.due_at).toLocaleDateString("ja-JP", {
                    timeZone: d.settings.timezone,
                    month: "short",
                    day: "numeric",
                  })}
                </Badge>
              </div>
            ))
          ) : (
            <Empty
              title="復習予定はまだありません"
              description="Drillを提出すると、理解度に合わせた復習が予定されます。"
            />
          )}
        </section>
        <section className="panel info-panel">
          <SectionTitle title="次に伸ばしたい概念" />
          {weak.length ? (
            weak.map((p) => (
              <Link
                className="weak-row"
                key={p.concept_id}
                to={`/concepts/${p.concept_id}`}
              >
                <span>
                  <small>{p.concept_id}</small>
                  <strong>
                    {concepts.find((c) => c.id === p.concept_id)?.title}
                  </strong>
                </span>
                <Badge color="gray">習熟度 {p.mastery_level}</Badge>
                <ArrowRight size={16} />
              </Link>
            ))
          ) : (
            <Empty
              title="学習から見つけていきましょう"
              description="解答が蓄積されると、優先して練習したい概念がわかります。"
            />
          )}
        </section>
      </div>
      <SectionTitle title="概念ごとの現在地" />
      <div className="concept-matrix">
        {concepts.map((c) => {
          const p = d.concepts.find((p) => p.concept_id === c.id);
          return (
            <Link
              to={`/concepts/${c.id}`}
              key={c.id}
              className={`matrix-cell ${p ? "measured" : ""}`}
            >
              <span>{c.id}</span>
              <strong>{p ? p.mastery_level : "—"}</strong>
              <small>{c.title}</small>
            </Link>
          );
        })}
      </div>
    </>
  );
}
export function History() {
  const [offset, setOffset] = useState(0),
    [expanded, setExpanded] = useState<string | null>(null);
  const { data, error, isPending } = useQuery({
    queryKey: ["history", offset],
    queryFn: () =>
      userApi<{ items: Attempt[]; total: number }>(
        `/history?limit=20&offset=${offset}`,
      ),
  });
  const { data: d } = useQuery(queries.dashboard);
  if (isPending) return <Loading />;
  if (error || !data) return <ErrorBox error={error} />;
  return (
    <>
      <PageTitle
        eyebrow="YOUR PRACTICE LOG"
        title="解答履歴"
        description="試行錯誤も、学習の一部。過去の実装を振り返りましょう。"
      />
      <div className="panel history-list">
        {data.items.length ? (
          data.items.map((a) => (
            <div className="history-entry" key={a.id}>
              <button
                className="history-row"
                onClick={() => setExpanded(expanded === a.id ? null : a.id)}
              >
                <span
                  className={
                    a.verdict === "Accepted" ? "history-ok" : "history-fail"
                  }
                >
                  <CheckCircle2 size={19} />
                </span>
                <div>
                  <strong>{a.problem_version_id}</strong>
                  <small>
                    {new Date(a.submitted_at).toLocaleString("ja-JP", {
                      timeZone: d?.settings.timezone ?? "Asia/Tokyo",
                    })}
                  </small>
                </div>
                <Badge color={a.verdict === "Accepted" ? "green" : "amber"}>
                  {a.verdict}
                </Badge>
                <span className="verification-badge">
                  {a.verification_level === "server_verified"
                    ? "正式検証"
                    : "暫定"}
                </span>
                <ArrowRight size={16} />
              </button>
              {expanded === a.id && (
                <div className="history-code">
                  <pre>{a.submitted_code}</pre>
                  <div className="history-meta">
                    <span>ヒント {a.hint_level_used}</span>
                    <span>
                      {a.result.passed_tests}/{a.result.total_tests} tests
                    </span>
                    <Link to={`/drill/s/${a.session_id}/${a.item_id}`}>
                      この問題を開く
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <Empty
            title="最初の1問から、記録が始まります"
            description="Drillでコードを提出すると、ここで実装と結果を振り返れます。"
          >
            <Link className="btn primary" to="/drill">
              Drillを始める
              <ArrowRight size={15} />
            </Link>
          </Empty>
        )}
      </div>
      {data.total > 20 && (
        <div className="pagination">
          <button
            className="btn secondary"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - 20))}
          >
            前へ
          </button>
          <span>
            {offset + 1}–{Math.min(offset + 20, data.total)} / {data.total}
          </span>
          <button
            className="btn secondary"
            disabled={offset + 20 >= data.total}
            onClick={() => setOffset(offset + 20)}
          >
            次へ
          </button>
        </div>
      )}
    </>
  );
}
