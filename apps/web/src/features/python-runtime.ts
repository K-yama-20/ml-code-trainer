import workerSource from "./python.worker.js?raw";
import frameSource from "./python.frame.js?raw";
import type { TuplePaths } from "../types/domain";

const indexURL = "https://cdn.jsdelivr.net/pyodide/v0.29.3/full/";
const timeoutResult = Symbol("timeout");
type Payload = Record<string, unknown>;
export interface WorkerResult {
  outputs: {
    value?: unknown;
    tuple_paths?: TuplePaths;
    error?: string;
    kind?: string;
    line?: number;
    mutated_inputs?: boolean;
    replaced_inputs?: boolean;
    wrong_type?: boolean;
  }[];
  stdout: string;
  stderr: string;
  static_ok: boolean;
}
interface Message {
  channel: string;
  id?: string;
  phase: string;
  message: string;
  elapsed_ms: number;
  result: WorkerResult;
  retire?: boolean;
}

let harness: Promise<string> | undefined;
function fetchHarness() {
  return (harness ??= fetch("/api/v1/runtime-harness", { credentials: "omit" })
    .then((res) => {
      if (!res.ok) throw new Error("実行ハーネスを読み込めませんでした。");
      return res.text();
    })
    .catch((e) => {
      harness = undefined;
      throw e;
    }));
}

class PythonRuntime {
  private channel = crypto.randomUUID();
  private frame = document.createElement("iframe");
  private request?: (data: Message) => void;
  private booting = true;
  private closed = false;
  private running = false;
  private failRequest?: (error: Error) => void;
  private preparation: Promise<void>;
  private preparedPackages = new Set<string>();
  private status?: (text: string) => void;
  private failStartup!: (error: Error) => void;
  private ready: Promise<void>;
  private startupTimer: number;

  constructor() {
    this.frame.sandbox.add("allow-scripts");
    this.frame.hidden = true;
    this.frame.title = "隔離されたPython実行環境";
    const script = `const channel=${JSON.stringify(this.channel)};\n${frameSource}`;
    this.frame.srcdoc = `<!doctype html><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; worker-src blob:; connect-src https://cdn.jsdelivr.net;"><script>${script.replace(/<\/script/gi, "<\\/script")}</script>`;
    const source = fetchHarness();
    // This can reject before the iframe announces readiness.
    void source.catch(() => {});
    this.ready = new Promise<void>((resolve, reject) => {
      this.failStartup = reject;
      this.request = (data) => {
        if (data.phase === "ready") {
          void source
            .then((harness) => {
              this.send(
                "init",
                { action: "init", indexURL, harness },
                workerSource,
              );
            })
            .catch(reject);
        } else if (data.phase === "initialized") {
          this.booting = false;
          clearTimeout(this.startupTimer);
          resolve();
        } else if (data.phase === "error") reject(new Error(data.message));
      };
    });
    this.preparation = this.ready;
    this.startupTimer = window.setTimeout(() => {
      this.failStartup(
        new Error("Python環境の読み込みがタイムアウトしました。"),
      );
    }, 120000);
    void this.ready.catch((error) => this.close(error));
    window.addEventListener("message", this.message);
    document.body.append(this.frame);
  }

  private message = (event: MessageEvent<Message>) => {
    if (
      event.source === this.frame.contentWindow &&
      event.data?.channel === this.channel
    )
      this.request?.(event.data);
  };
  private send(command: string, payload?: Payload, bootstrap?: string) {
    if (!this.closed)
      this.frame.contentWindow?.postMessage(
        { channel: this.channel, command, payload, bootstrap },
        "*",
      );
  }

  close(error = new Error("Python環境を停止しました。")) {
    if (this.closed) return;
    this.send("stop");
    this.closed = true;
    clearTimeout(this.startupTimer);
    if (this.booting) this.failStartup(error);
    this.failRequest?.(error);
    this.request = undefined;
    this.failRequest = undefined;
    window.removeEventListener("message", this.message);
    const frame = this.frame;
    window.setTimeout(() => frame.remove(), 0);
    if (shared === this) shared = undefined;
  }

  prepare(packages: string[]) {
    const preparation = this.preparation
      .then(async () => {
        if (this.closed) throw new Error("Python環境を停止しました。");
        const missing = packages.filter(
          (name) => !this.preparedPackages.has(name),
        );
        if (!missing.length) return;
        await new Promise<void>((resolve, reject) => {
          const id = crypto.randomUUID();
          const timer = window.setTimeout(() => {
            reject(new Error("Pythonパッケージの準備がタイムアウトしました。"));
            this.close();
          }, 120000);
          const done = () => {
            clearTimeout(timer);
            this.failRequest = undefined;
          };
          this.failRequest = (error) => {
            done();
            reject(error);
          };
          this.request = (data) => {
            if (data.id !== id) return;
            if (data.phase === "packages") this.status?.(data.message);
            if (data.phase === "prepared") {
              missing.forEach((name) => this.preparedPackages.add(name));
              done();
              resolve();
            } else if (data.phase === "error") {
              done();
              reject(new Error(data.message));
              this.close();
            }
          };
          this.send("prepare", { action: "prepare", id, packages: missing });
        });
      })
      .catch((error) => {
        this.close(error);
        throw error;
      });
    this.preparation = preparation;
    return preparation;
  }

  async run(
    payload: Payload,
    onStatus: (text: string) => void,
    signal: AbortSignal,
  ) {
    if (this.running)
      throw new Error("前のPython実行が終わるまでお待ちください。");
    this.running = true;
    this.status = onStatus;
    let timer = 0;
    let fail!: (error: Error) => void;
    const aborted = () => {
      fail(new DOMException("実行を中止しました。", "AbortError"));
      this.close();
    };
    try {
      return await new Promise<Message | typeof timeoutResult>(
        (resolve, reject) => {
          fail = reject;
          signal.addEventListener("abort", aborted, { once: true });
          if (signal.aborted) return aborted();
          if (this.booting) onStatus("Pythonを起動しています…");
          void this.prepare((payload.packages as string[]) ?? [])
            .then(() => {
              if (signal.aborted) return;
              if (this.closed) throw new Error("Python環境を停止しました。");
              this.failRequest = reject;
              const id = crypto.randomUUID();
              this.request = (data) => {
                if (data.id !== id) return;
                if (data.phase === "packages") onStatus(data.message);
                if (data.phase === "running") {
                  onStatus("");
                  clearTimeout(timer);
                  timer = window.setTimeout(() => {
                    resolve(timeoutResult);
                    this.close();
                  }, 5000);
                }
                if (data.phase === "error") {
                  reject(new Error(data.message));
                  this.close();
                }
                if (data.phase === "complete") {
                  resolve(data);
                  if (data.retire) {
                    this.close();
                    if (activeUsers) {
                      void runtime()
                        .prepare((payload.packages as string[]) ?? [])
                        .catch(() => {
                          // A failed replacement stays stopped until the next explicit run.
                        });
                    }
                  }
                }
              };
              timer = window.setTimeout(() => {
                reject(
                  new Error("Pythonパッケージの準備がタイムアウトしました。"),
                );
                this.close();
              }, 120000);
              this.send("run", { ...payload, action: "run", id });
            })
            .catch(reject);
        },
      );
    } finally {
      this.running = false;
      this.status = undefined;
      this.failRequest = undefined;
      clearTimeout(timer);
      signal.removeEventListener("abort", aborted);
    }
  }
}
let shared: PythonRuntime | undefined;
let activeUsers = 0;
const runtime = () => (shared ??= new PythonRuntime());
export function keepPythonActive() {
  activeUsers++;
  return () => {
    activeUsers--;
    if (!activeUsers) shared?.close();
  };
}
export function warmPython() {
  runtime();
}
export function runInPython(
  payload: Payload,
  status: (text: string) => void,
  signal: AbortSignal,
) {
  return runtime().run(payload, status, signal);
}
export { timeoutResult };
