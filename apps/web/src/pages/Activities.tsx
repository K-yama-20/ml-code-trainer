import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  FileCode2,
  FolderOpen,
  Layers,
  Lightbulb,
  Network,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { api, queries, refreshLearning, userApi } from "../lib/api";
import {
  Badge,
  Button,
  ErrorBox,
  Loading,
  PageTitle,
  ProgressBar,
} from "../components/ui";
import { CodeEditor } from "../components/CodeEditor";
import type { Activity, Question } from "../types/domain";

export function QuestionCard({
  activity,
  question,
  number,
  onJump,
}: {
  activity: Activity;
  question: Question;
  number: number;
  onJump?: () => void;
}) {
  const [selected, setSelected] = useState<number | null>(null),
    [result, setResult] = useState<{
      accepted: boolean;
      explanation: string;
      correct_answer: number;
    } | null>(null),
    [error, setError] = useState<unknown>(null),
    [busy, setBusy] = useState(false);
  async function check() {
    if (selected === null) return;
    setBusy(true);
    try {
      setResult(
        await userApi(`/activities/${activity.id}/answers`, {
          method: "POST",
          body: JSON.stringify({ question_id: question.id, answer: selected }),
        }),
      );
      await refreshLearning();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="question-card panel">
      <div className="question-heading">
        <Badge color="gray">QUESTION {String(number).padStart(2, "0")}</Badge>
        {question.file && (
          <button className="text-link" onClick={onJump}>
            <FileCode2 size={13} />
            {question.file}
            <ChevronRight size={14} />
          </button>
        )}
      </div>
      <h3>{question.prompt}</h3>
      <div
        className="answer-options"
        role="radiogroup"
        aria-label={question.prompt}
      >
        {question.choices.map((choice, i) => (
          <button
            role="radio"
            aria-checked={selected === i}
            className={`${selected === i ? "selected" : ""} ${result && i === result.correct_answer ? "correct" : ""}`}
            key={i}
            onClick={() => {
              setSelected(i);
              setResult(null);
            }}
          >
            <span>{String.fromCharCode(65 + i)}</span>
            {choice}
            {result && i === result.correct_answer && <Check size={16} />}
          </button>
        ))}
      </div>
      <Button
        variant="secondary"
        disabled={selected === null || busy}
        onClick={check}
      >
        {busy ? "確認中…" : "回答を確認"}
        <ArrowRight size={15} />
      </Button>
      {result && (
        <div
          role="status"
          className={`activity-feedback ${result.accepted ? "correct" : "incorrect"}`}
        >
          <strong>
            {result.accepted
              ? "正解です"
              : "もう一度、コードの流れを確認しましょう"}
          </strong>
          <p>{result.explanation}</p>
        </div>
      )}
      {!!error && <ErrorBox error={error} />}
    </section>
  );
}
export function ReadingList() {
  const {
    data: projects = [],
    error,
    isPending,
  } = useQuery({
    queryKey: ["reading"],
    queryFn: () => api<Activity[]>("/reading-projects"),
  });
  const { data: deep = [] } = useQuery({
    queryKey: ["deep"],
    queryFn: () => api<Activity[]>("/deep-dives"),
  });
  const { data: d } = useQuery(queries.dashboard);
  if (isPending) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  return (
    <>
      <PageTitle
        eyebrow="CONNECT THE DOTS"
        title="コードの流れを、読み解く。"
        description="ファイルをまたぐデータの流れを追い、ひとつのプロジェクトを理解する。"
      />
      <div className="reading-list">
        {projects.map((p, i) => {
          const answered =
            d?.activities.filter((a) => a.activity_id === p.id && a.accepted)
              .length ?? 0;
          return (
            <Link
              to={`/reading/${p.id}`}
              className="reading-project-card panel"
              key={p.id}
            >
              <div className={`reading-art art-${i}`}>
                <div className="art-file">
                  <FileCode2 size={26} />
                  <span>{p.files?.length} files</span>
                </div>
                <Network className="art-network" size={100} />
                <span className="art-language">{p.library}</span>
              </div>
              <div className="reading-project-copy">
                <div className="tag-row">
                  <Badge>{p.library}</Badge>
                  <span className="muted">PROJECT 0{i + 1}</span>
                </div>
                <h2>{p.title}</h2>
                <p>{p.description}</p>
                <div className="project-meta">
                  <span>{p.line_count}行</span>
                  <span>{p.questions.length}設問</span>
                  <span>約{p.minutes}分</span>
                </div>
                <ProgressBar value={(answered / 8) * 100} />
                <div className="concept-card-bottom">
                  <span>{answered}/8 正解</span>
                  <span>
                    プロジェクトを開く
                    <ArrowRight size={15} />
                  </span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
      <PageTitle
        eyebrow="DEEPEN YOUR UNDERSTANDING"
        level={2}
        title="Deep Dive"
        description="shapeやデータフローを図で追い、仕組みまで理解する。"
      />
      <div className="deep-grid">
        {deep.map((t, i) => (
          <Link
            to={`/deep-dive/${t.id}`}
            className="deep-card panel"
            key={t.id}
          >
            <span className="deep-number">
              {String(i + 1).padStart(2, "0")}
            </span>
            <Lightbulb size={22} />
            <h3>{t.title}</h3>
            <span className="deep-card-bottom">
              {t.concept_id}
              <ArrowRight size={16} />
            </span>
          </Link>
        ))}
      </div>
    </>
  );
}
export function DeepDive() {
  const { taskId } = useParams();
  const {
    data: t,
    error,
    isPending,
  } = useQuery({
    queryKey: ["deep", taskId],
    queryFn: () => api<Activity>(`/deep-dives/${taskId}`),
  });
  const { data: d } = useQuery(queries.dashboard);
  if (isPending) return <Loading />;
  if (error || !t) return <ErrorBox error={error} />;
  return (
    <>
      <Link className="back-link" to="/reading">
        <ArrowLeft size={15} />
        すべての学習コンテンツ
      </Link>
      <PageTitle
        eyebrow="DEEP DIVE / THINK IN SHAPES"
        title={t.title}
        description="コードを追い、結果を予測して、理解を確かめましょう。"
      />
      <div className="deep-layout">
        <section className="panel deep-code">
          <div className="editor-heading">
            <FileCode2 size={15} />
            explore.py<Badge color="gray">コードを読む</Badge>
          </div>
          <div style={{ height: 260 }}>
            <CodeEditor
              value={t.code ?? ""}
              readOnly
              theme={d?.settings.theme}
              fontSize={d?.settings.font_size}
            />
          </div>
          <div className="flow-section">
            <h3>
              <Layers size={17} />
              データフローを追う
            </h3>
            <div className="shape-flow">
              {t.flow?.map((node, i) => (
                <div className="flow-step" key={i}>
                  <div>
                    <span>0{i + 1}</span>
                    <strong>{node}</strong>
                  </div>
                  {i < (t.flow?.length ?? 0) - 1 && <ArrowRight size={20} />}
                </div>
              ))}
            </div>
            <p className="muted">
              各ステップで、値とshapeがどう変わるかを確認してください。
            </p>
          </div>
        </section>
        <div>
          {t.questions.map((q, i) => (
            <QuestionCard key={q.id} activity={t} question={q} number={i + 1} />
          ))}
        </div>
      </div>
    </>
  );
}
export function ReadingProject() {
  const { projectId } = useParams();
  const {
    data: p,
    error,
    isPending,
  } = useQuery({
    queryKey: ["reading", projectId],
    queryFn: () => api<Activity>(`/reading-projects/${projectId}`),
  });
  const [file, setFile] = useState(""),
    [jump, setJump] = useState(1),
    [qi, setQi] = useState(0);
  const { data: d } = useQuery(queries.dashboard);
  if (isPending) return <Loading />;
  if (error || !p) return <ErrorBox error={error} />;
  const current =
    p.files?.find((f) => f.name === (file || p.entry)) ?? p.files?.[0];
  function go(name: string, symbol?: string) {
    setFile(name);
    const target = p!.files
      ?.find((f) => f.name === name)
      ?.symbols.find((s) => s.name === symbol);
    setJump(target?.line ?? 1);
  }
  const q = p.questions[qi];
  return (
    <div className="reading-workspace">
      <Link className="back-link" to="/reading">
        <ArrowLeft size={15} />
        Code Reading
      </Link>
      <PageTitle eyebrow={`${p.library} / PROJECT READING`} title={p.title}>
        <Badge color="gray">
          {p.line_count}行 · {p.files?.length}ファイル
        </Badge>
      </PageTitle>
      <div className="reading-panes panel">
        <aside className="file-tree">
          <div className="tree-title">
            <FolderOpen size={15} />
            EXPLORER
          </div>
          {p.files?.map((f) => (
            <div key={f.name}>
              <button
                className={current?.name === f.name ? "active" : ""}
                onClick={() => go(f.name)}
              >
                <FileCode2 size={14} />
                {f.name}
              </button>
              {current?.name === f.name && (
                <div className="symbol-list">
                  {f.symbols.map((s, i) => (
                    <button key={i} onClick={() => go(f.name, s.name)}>
                      <span>ƒ</span>
                      {s.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </aside>
        <div className="reading-code">
          <div className="editor-heading">
            <FileCode2 size={14} />
            {current?.name}
            <small>Python · 読み取り専用</small>
          </div>
          <div className="reading-editor">
            <CodeEditor
              value={current?.code ?? ""}
              readOnly
              jump={jump}
              fontSize={d?.settings.font_size ?? 13}
              theme={d?.settings.theme}
            />
          </div>
          <div className="definition-jumps">
            <label>
              定義へジャンプ
              <select
                aria-label="関数定義へジャンプ"
                value=""
                onChange={(e) => {
                  const [f, s] = e.target.value.split(":");
                  go(f, s);
                }}
              >
                <option value="">関数を選択…</option>
                {p.files?.flatMap((f) =>
                  f.symbols.map((s, i) => (
                    <option
                      key={`${f.name}-${i}`}
                      value={`${f.name}:${s.name}`}
                    >
                      {f.name} → {s.name}
                    </option>
                  )),
                )}
              </select>
            </label>
          </div>
        </div>
        <aside className="reading-questions">
          <div className="question-progress">
            <BookOpen size={17} />
            <span>理解を確かめる</span>
            <strong>{qi + 1}/8</strong>
          </div>
          <ProgressBar value={((qi + 1) / 8) * 100} />
          <QuestionCard
            key={q.id}
            activity={p}
            question={q}
            number={qi + 1}
            onJump={() => go(q.file!, q.symbol)}
          />
          <div className="question-nav">
            <Button
              variant="ghost"
              disabled={qi === 0}
              onClick={() => setQi(qi - 1)}
            >
              <ArrowLeft size={15} />
              前へ
            </Button>
            <Button
              variant="secondary"
              disabled={qi === 7}
              onClick={() => setQi(qi + 1)}
            >
              次の設問
              <ArrowRight size={15} />
            </Button>
          </div>
        </aside>
      </div>
    </div>
  );
}
