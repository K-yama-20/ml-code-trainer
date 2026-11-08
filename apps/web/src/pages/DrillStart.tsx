import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  Code2,
  Layers,
  Play,
  RotateCcw,
  SlidersHorizontal,
  Target,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { newSession, problemCount, queries, sessionPath } from "../lib/api";
import { Badge, Button, ErrorBox, PageTitle } from "../components/ui";
import type { Stage } from "../types/domain";
export function DrillStart() {
  const { data: d } = useQuery(queries.dashboard),
    { data: modules = [] } = useQuery(queries.modules),
    { data: concepts } = useQuery(queries.concepts),
    navigate = useNavigate();
  const [count, setCount] = useState(20),
    [selected, setSelected] = useState<string[]>([]),
    [stages, setStages] = useState<Stage[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<unknown>(null);
  async function start(kind: string) {
    setBusy(true);
    setError(null);
    try {
      navigate(
        sessionPath(
          await newSession({ kind, count, modules: selected, stages }),
        ),
      );
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="WRITE. RUN. UNDERSTAND."
        title="手を動かす、理解が深まる。"
        description="1問ずつの小さな実装を、コードを読む力に変えていきましょう。"
      />
      {error && <ErrorBox error={error} />}{" "}
      {d?.current_session && (
        <div className="resume-strip panel">
          <Play size={20} />
          <div>
            <strong>途中のセッションがあります</strong>
            <p>
              {d.current_session.position + 1} /{" "}
              {d.current_session.items.length}問目から再開
            </p>
          </div>
          <Button onClick={() => navigate(sessionPath(d.current_session!))}>
            学習を再開
            <ArrowRight size={17} />
          </Button>
        </div>
      )}
      <div className="drill-mode-grid">
        {[
          {
            kind: "daily",
            title: "Daily Drill",
            icon: Target,
            badge: "おすすめ",
            text: "進捗に合わせて復習と新しい問題を選びます。目標数を超えても続けられます。",
            button: "今日のDrillを始める",
          },
          {
            kind: "review",
            title: "Review",
            icon: RotateCcw,
            badge: `${d?.due_count ?? 0}概念`,
            text: "ちょうど忘れかけるタイミングで。別の問題や入力で、理解を確かめます。",
            button: "復習を始める",
          },
        ].map(({ icon: Icon, ...m }) => (
          <section className="mode-card panel" key={m.kind}>
            <div className="mode-icon">
              <Icon size={27} />
            </div>
            <Badge>{m.badge}</Badge>
            <h2>{m.title}</h2>
            <p>{m.text}</p>
            <Button disabled={busy} onClick={() => start(m.kind)}>
              {m.button}
              <ArrowRight size={17} />
            </Button>
          </section>
        ))}
      </div>
      <section className="custom-drill panel">
        <div className="section-title">
          <h2>
            <SlidersHorizontal size={20} />
            Custom Drill
          </h2>
          <Badge color="gray">自分のペースで</Badge>
        </div>
        <div className="custom-grid">
          <div>
            <h3>ライブラリ</h3>
            <div className="toggle-group">
              {modules.map((m) => (
                <button
                  className={selected.includes(m.id) ? "selected" : ""}
                  key={m.id}
                  onClick={() =>
                    setSelected((v) =>
                      v.includes(m.id)
                        ? v.filter((id) => id !== m.id)
                        : [...v, m.id],
                    )
                  }
                >
                  {m.title}
                </button>
              ))}
            </div>
            <p className="muted">選択しない場合は全分野から出題します。</p>
          </div>
          <div>
            <h3>ステージ</h3>
            <div className="toggle-group">
              {(["guided", "partial", "independent"] as Stage[]).map((s) => (
                <button
                  className={stages.includes(s) ? "selected" : ""}
                  key={s}
                  onClick={() =>
                    setStages((v) =>
                      v.includes(s) ? v.filter((id) => id !== s) : [...v, s],
                    )
                  }
                >
                  {s}
                </button>
              ))}
            </div>
            <h3>問題数</h3>
            <div className="toggle-group">
              {[10, 20, 30, 50].map((n) => (
                <button
                  className={count === n ? "selected" : ""}
                  key={n}
                  onClick={() => setCount(n)}
                >
                  {n}問
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="custom-bottom">
          <span>
            <Layers size={16} />
            {concepts &&
              `${problemCount(concepts)}問・${concepts.length}概念から構成`}
          </span>
          <Button
            variant="secondary"
            disabled={busy}
            onClick={() => start("custom")}
          >
            <Code2 size={16} />
            カスタムDrillを始める
            <ArrowRight size={17} />
          </Button>
        </div>
      </section>
    </>
  );
}
