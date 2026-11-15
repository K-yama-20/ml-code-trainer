import initSqlite from "@sqlite.org/sqlite-wasm";
import { runSql } from "./sql-engine";
import type { SqlProblem } from "../types/domain";

export interface SqlRequest {
  id: string;
  sql: SqlProblem;
  code: string;
  preview: boolean;
  tolerance: number;
}

const sqlite = initSqlite();
void sqlite.then(
  () => self.postMessage({ ready: true }),
  () => self.postMessage({ ready: false }),
);
self.onmessage = async ({ data }: MessageEvent<SqlRequest>) => {
  const { id, sql, code, preview, tolerance } = data;
  self.postMessage({
    id,
    result: runSql(await sqlite, sql, code, preview, tolerance),
  });
};
