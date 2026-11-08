import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  BookOpen,
  Braces,
  Check,
  ChevronRight,
  Code2,
  Flame,
  Play,
  RotateCcw,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { newSession, queries, sessionPath } from "../lib/api";
import {
  Badge,
  Button,
  ErrorBox,
  Loading,
  ProgressBar,
  SectionTitle,
} from "../components/ui";
export function Home() {
  const { data: d, error, isPending } = useQuery(queries.dashboard);
  const { data: modules = [] } = useQuery(queries.modules);
  const navigate = useNavigate(),
    [busy, setBusy] = useState(false),
    [actionError, setActionError] = useState<unknown>(null);
  async function start(review = false) {
    setBusy(true);
    try {
      if (d?.current_session && !review)
        navigate(sessionPath(d.current_session));
      else
        navigate(
          sessionPath(await newSession({ kind: review ? "review" : "daily" })),
        );
    } catch (e) {
      setActionError(e);
    } finally {
      setBusy(false);
    }
  }
  if (isPending) return <Loading />;
  if (error || !d) return <ErrorBox error={error} />;
  const goal = d.settings.daily_goal,
    rate = Math.round((d.accepted / Math.max(1, d.total_attempts)) * 100);
  return (
    <div className="home-page">
      <div className="home-greeting">
        <div>
          <span className="eyebrow">YOUR LEARNING WORKSPACE</span>
          <h1>今日も、コードを読む力を。</h1>
          <p>小さく書いて、動かして、理解する。今日の一歩を始めましょう。</p>
        </div>
        <div className="date-chip">
          <span className="status-dot" />
          学習の準備ができています
        </div>
      </div>
      {!!actionError && <ErrorBox error={actionError} />}
      <div className="home-top-grid">
        <section className="continue-card">
          <div className="hero-grid" />
          <div className="continue-copy">
            <div className="hero-kicker">
              <span className="hero-dot" />
              DAILY PRACTICE<Badge color="subtle">1問 約1–3分</Badge>
            </div>
            <h2>
              ひとつ書くたび、
              <br />
              読めるコードが増えていく。
            </h2>
            <p>
              {d.current_session
                ? "前回の続きから、思考をつなげましょう。"
                : "まずは短いDrillから。手を動かして、理解を確かめましょう。"}
            </p>
            <Button onClick={() => start()} disabled={busy}>
              <Play size={16} fill="currentColor" />
              {busy ? "準備中…" : "学習を再開"}
              <ArrowRight size={17} />
            </Button>
            <span className="hero-caption">
              {d.current_session
                ? `第${d.current_session.position + 1}問から再開できます`
                : "登録不要で始められます"}
            </span>
          </div>
          <div className="hero-code" aria-hidden="true">
            <div className="hero-code-header">
              <i />
              <i />
              <i />
              <span>one_step.py</span>
            </div>
            <code>
              <span className="code-comment"># 小さな一歩を、積み重ねる</span>
              <br />
              <span className="code-purple">import</span> numpy{" "}
              <span className="code-purple">as</span> np
              <br />
              <br />x = np.array([[<em>1</em>, <em>2</em>], [<em>3</em>,{" "}
              <em>4</em>]])
              <br />
              means = x.mean(axis=<em>1</em>)<br />
              <br />
              <span className="code-green">print</span>(means)
              <br />
              <span className="code-comment"># → [1.5, 3.5]</span>
            </code>
            <div className="hero-code-bottom">
              <Check size={13} />
              理解は、実行から始まる。
            </div>
          </div>
        </section>
        <section className="goal-card panel">
          <div className="goal-heading">
            <span>
              <Target size={18} />
              今日の目標
            </span>
            <Link to="/settings" aria-label="目標を設定">
              設定
              <ChevronRight size={13} />
            </Link>
          </div>
          <div
            className="goal-ring"
            style={
              {
                "--progress": `${Math.min(100, (d.today_count / goal) * 100)}%`,
              } as React.CSSProperties
            }
          >
            <div>
              <strong>
                {d.today_count}
                <span> / {goal}</span>
              </strong>
              <small>問の演習を提出</small>
            </div>
          </div>
          <div className="goal-bottom">
            <Flame size={18} />
            <strong>{d.streak}日</strong>
            <span>連続学習中</span>
          </div>
        </section>
      </div>
      <div className="stats-row">
        {[
          {
            icon: Code2,
            label: "累計解答数",
            value: d.total_attempts,
            unit: "問",
            note: "一つひとつが、理解の積み重ね",
          },
          {
            icon: Braces,
            label: "習得済み概念",
            value: d.mastered,
            unit: "/ 30",
            note: "自力実装の正式検証を含む",
          },
          {
            icon: TrendingUp,
            label: "正答率",
            value: d.total_attempts ? rate : "—",
            unit: d.total_attempts ? "%" : "",
            note: d.total_attempts
              ? "これまでの全提出から算出"
              : "初めての提出から記録します",
          },
          {
            icon: RotateCcw,
            label: "今日の復習",
            value: d.due_count,
            unit: "概念",
            note: d.due_count
              ? "記憶を定着させるチャンス"
              : "復習は学習に合わせて届きます",
          },
        ].map(({ icon: Icon, ...s }) => (
          <div className="stat-card" key={s.label}>
            <div className="stat-top">
              <span>{s.label}</span>
              <Icon size={17} />
            </div>
            <div className="stat-value">
              {s.value}
              <span>{s.unit}</span>
            </div>
            <p>{s.note}</p>
          </div>
        ))}
      </div>
      <div className="home-middle-grid">
        <section>
          <SectionTitle title="今日のおすすめ" />
          <div className="recommendations">
            <Link to="/concepts/NP05" className="recommendation panel">
              <span className="recommend-icon blue">
                <Braces size={23} />
              </span>
              <div>
                <div className="recommend-tags">
                  <Badge>NumPy</Badge>
                  <small>Drill · 約2分</small>
                </div>
                <h3>axisとshapeを、手で覚える</h3>
                <p>行と列の平均。短いコードで違いを確かめよう。</p>
              </div>
              <ArrowRight size={18} />
            </Link>
            <Link to="/deep-dive/broadcast" className="recommendation panel">
              <span className="recommend-icon violet">
                <Zap size={23} />
              </span>
              <div>
                <div className="recommend-tags">
                  <Badge color="violet">Deep Dive</Badge>
                  <small>理解を深める · 約3分</small>
                </div>
                <h3>Broadcastingを読み解く</h3>
                <p>配列のshapeがどう広がるのか、図で理解する。</p>
              </div>
              <ArrowRight size={18} />
            </Link>
          </div>
        </section>
        <section>
          <SectionTitle
            title="今週のアクティビティ"
            to="/analytics"
            label="学習分析"
          />
          <div className="activity-card panel">
            <div className="activity-total">
              <strong>
                {d.weekly.reduce((s, x) => s + x.count, 0)}
                <span>問</span>
              </strong>
              <span>この7日間に提出</span>
              <span className="activity-legend">
                <i />
                解答数
              </span>
            </div>
            <div className="week-chart">
              {d.weekly.map((day, i) => (
                <div className="week-column" key={day.date}>
                  <div
                    className={`week-bar ${i === 6 ? "today" : ""}`}
                    style={{
                      height: `${Math.max(4, (day.count / Math.max(1, ...d.weekly.map((x) => x.count))) * 84)}px`,
                    }}
                    title={`${day.date}: ${day.count}問`}
                  />
                  <span>
                    {new Date(day.date + "T12:00:00").toLocaleDateString(
                      "ja-JP",
                      { weekday: "short" },
                    )}
                  </span>
                </div>
              ))}
            </div>
            <div className="activity-caption">
              {d.total_attempts
                ? "無理のないペースで、学びを続けましょう。"
                : "最初の1問を解くと、ここに学習が記録されます。"}
            </div>
          </div>
        </section>
      </div>
      <SectionTitle
        title="学習カリキュラム"
        to="/curriculum"
        label="カリキュラムを見る"
      />
      <div className="module-grid">
        {modules.map((m, i) => {
          const count = [3, 9, 4, 4, 10][i];
          const ps = d.concepts.filter((c) =>
            c.concept_id.startsWith(["PY", "NP", "PD", "SK", "PT"][i]),
          );
          return (
            <Link
              className="module-card panel"
              to={`/curriculum/${m.id}`}
              key={m.id}
            >
              <div className="module-top">
                <span
                  className="module-monogram"
                  style={{ color: m.color, background: `${m.color}14` }}
                >
                  {["Py", "np", "pd", "sk", "pt"][i]}
                </span>
                <ChevronRight size={16} />
              </div>
              <h3>{m.title}</h3>
              <p>
                {count}概念<span>·</span>
                {count * 6}問
              </p>
              <ProgressBar
                value={
                  (ps.reduce((s, p) => s + p.mastery_level, 0) / (count * 5)) *
                  100
                }
                color={m.color}
              />
              <small>{ps.length ? `${ps.length}概念を学習中` : "未学習"}</small>
            </Link>
          );
        })}
      </div>
      <div className="home-reading">
        <BookOpen size={21} />
        <div>
          <strong>コードの「点」を、プロジェクトの「線」に。</strong>
          <span>
            3つの実践プロジェクトで、ファイルをまたぐデータの流れを読み解こう。
          </span>
        </div>
        <Link to="/reading">
          Code Readingへ
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
