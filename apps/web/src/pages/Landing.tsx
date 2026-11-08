import { useQuery } from "@tanstack/react-query";
import { problemCount, queries } from "../lib/api";
import {
  ArrowRight,
  Braces,
  Check,
  Code2,
  Layers,
  Play,
  Terminal,
} from "lucide-react";
import { Link } from "react-router-dom";
export function Landing() {
  const { data: concepts } = useQuery(queries.concepts);
  return (
    <div className="landing">
      <header>
        <Link to="/" className="brand">
          <span className="brand-mark">
            <Code2 size={23} />
          </span>
          <span>
            ML Code<span className="brand-light">Trainer</span>
          </span>
        </Link>
        <nav>
          <a href="#how">学び方</a>
          <a href="#curriculum">カリキュラム</a>
          <Link className="btn secondary" to="/home">
            学習を始める
            <ArrowRight size={15} />
          </Link>
        </nav>
      </header>
      <main>
        <div className="landing-hero">
          <div className="landing-hero-copy">
            <span className="eyebrow">
              <span className="status-dot" />
              LEARN TO READ MACHINE LEARNING CODE
            </span>
            <h1>
              書いた分だけ、
              <br />
              <span>コードが読める。</span>
            </h1>
            <p>
              機械学習のコードを、読む力に変える。
              <br />
              短いPython演習を積み重ねて、AIが書いたコードの
              <br className="desktop-break" />
              「何をしているか」まで理解しよう。
            </p>
            <div className="landing-actions">
              <Link className="btn primary" to="/home">
                <Play size={16} fill="currentColor" />
                無料で学習を始める
                <ArrowRight size={18} />
              </Link>
              <span>
                <Check size={14} />
                登録不要でスタート
              </span>
            </div>
            <div className="landing-libraries">
              Python<span>/</span>NumPy<span>/</span>Pandas<span>/</span>
              scikit-learn<span>/</span>PyTorch
            </div>
          </div>
          <div className="landing-terminal">
            <div className="terminal-title">
              <div>
                <i />
                <i />
                <i />
              </div>
              <span>your_first_step.py</span>
              <Terminal size={14} />
            </div>
            <div className="terminal-code">
              <div>
                <small>1</small>
                <span>
                  <b>import</b> numpy <b>as</b> np
                </span>
              </div>
              <div>
                <small>2</small>
              </div>
              <div>
                <small>3</small>
                <span className="code-comment"># 各行の平均を求める</span>
              </div>
              <div>
                <small>4</small>
                <span>
                  x = np.array([[<em>1</em>, <em>2</em>], [<em>3</em>,{" "}
                  <em>4</em>]])
                </span>
              </div>
              <div>
                <small>5</small>
                <span>
                  result = x.mean(axis=<em>1</em>)
                </span>
              </div>
              <div>
                <small>6</small>
              </div>
              <div>
                <small>7</small>
                <span>
                  <b>print</b>(result)
                </span>
              </div>
            </div>
            <div className="terminal-result">
              <span>
                <Check size={15} />
                Accepted
              </span>
              <code>[1.5 3.5]</code>
              <small>サンプルコードの実行結果</small>
            </div>
            <div className="terminal-caption">
              Write.<span>Run.</span>Understand.
            </div>
          </div>
        </div>
        <section id="how" className="landing-how">
          <div>
            <span className="eyebrow">SMALL STEPS. REAL UNDERSTANDING.</span>
            <h2>見るだけで終わらない、3段階の学習。</h2>
          </div>
          <div className="landing-steps">
            {[
              {
                icon: Braces,
                name: "Guided",
                text: "空欄を埋めながら、頻出パターンを覚える。",
              },
              {
                icon: Code2,
                name: "Partial",
                text: "APIと引数を選び、自分で処理を書いてみる。",
              },
              {
                icon: Layers,
                name: "Independent",
                text: "条件から実装を組み立て、確かな理解へ。",
              },
            ].map(({ icon: Icon, ...s }, i) => (
              <article key={s.name}>
                <span>0{i + 1}</span>
                <Icon size={25} />
                <h3>{s.name}</h3>
                <p>{s.text}</p>
              </article>
            ))}
          </div>
        </section>
        <section id="curriculum" className="landing-curriculum">
          <div>
            <h2>毎日出会うコードを、ひとつずつ。</h2>
            <p>
              {concepts
                ? `${concepts.length}概念・${problemCount(concepts)}問のDrill`
                : "Drill"}
              、12のDeep Dive、3つの読解プロジェクト。
            </p>
          </div>
          <Link className="btn secondary" to="/curriculum">
            カリキュラムを見る
            <ArrowRight size={16} />
          </Link>
        </section>
      </main>
      <footer>
        <span>© ML Code Trainer</span>
        <span>Write. Run. Understand.</span>
      </footer>
    </div>
  );
}
