import type { Result, SqlProblem } from "../types/domain";
import type { SqlRequest } from "./sql.worker";

let worker: Worker | undefined;
let ready: Promise<void> | undefined;
let cancelStartup: (() => void) | undefined;

export function stopSql() {
  const cancel = cancelStartup;
  cancelStartup = undefined;
  worker?.terminate();
  worker = undefined;
  ready = undefined;
  cancel?.();
}

export async function warmSql() {
  if (ready) return ready;
  const instance = new Worker(new URL("./sql.worker.ts", import.meta.url), {
    type: "module",
  });
  worker = instance;
  ready = new Promise<void>((resolve, reject) => {
    const timeout = window.setTimeout(() => fail(), 15000);
    const finish = () => {
      clearTimeout(timeout);
      instance.removeEventListener("error", fail);
      instance.removeEventListener("message", initialized);
      if (worker === instance) cancelStartup = undefined;
    };
    const fail = () => {
      finish();
      if (worker === instance) stopSql();
      reject(
        new Error("SQLiteを読み込めませんでした。もう一度お試しください。"),
      );
    };
    const initialized = ({ data }: MessageEvent<{ ready: boolean }>) => {
      if (!data.ready) return fail();
      finish();
      resolve();
    };
    cancelStartup = fail;
    instance.addEventListener("error", fail, { once: true });
    instance.addEventListener("message", initialized, { once: true });
  });
  return ready;
}

export async function browserSql(
  sql: SqlProblem,
  code: string,
  preview: boolean,
  tolerance: number,
  status: (message: string) => void,
  signal: AbortSignal,
): Promise<Result> {
  signal.throwIfAborted();
  status("SQLiteを準備しています…");
  const startup = warmSql();
  const instance = worker!;
  return new Promise<Result>((resolve, reject) => {
    let timer = 0;
    const finish = () => {
      clearTimeout(timer);
      signal.removeEventListener("abort", abort);
      instance.removeEventListener("error", fail);
      instance.removeEventListener("message", receive);
    };
    const abort = () => {
      finish();
      if (worker === instance) stopSql();
      reject(new DOMException("実行を中止しました。", "AbortError"));
    };
    const fail = () => {
      finish();
      if (worker === instance) stopSql();
      reject(
        new Error(
          "SQLiteの実行を続けられませんでした。もう一度お試しください。",
        ),
      );
    };
    const id = crypto.randomUUID();
    const receive = ({
      data,
    }: MessageEvent<{ id: string; result: Result }>) => {
      if (data.id !== id) return;
      finish();
      resolve(data.result);
    };
    signal.addEventListener("abort", abort, { once: true });
    void startup
      .then(() => {
        if (signal.aborted) return;
        status("");
        instance.addEventListener("message", receive);
        instance.addEventListener("error", fail, { once: true });
        timer = window.setTimeout(() => {
          finish();
          if (worker === instance) stopSql();
          resolve({
            verdict: "Time Limit Exceeded",
            passed_tests: 0,
            total_tests: preview ? 1 : sql.cases.length,
            stderr:
              "実行時間の上限を超えました。結合や絞り込みの条件を確認してください。",
            preview,
          });
        }, 3000);
        instance.postMessage({
          id,
          sql,
          code,
          preview,
          tolerance,
        } satisfies SqlRequest);
      })
      .catch(fail);
  });
}
