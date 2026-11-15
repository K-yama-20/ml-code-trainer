import type { Sqlite3Static } from "@sqlite.org/sqlite-wasm";
import type {
  Result,
  SqlCell,
  SqlProblem,
  SqlResultTable,
} from "../types/domain";

const encoder = new TextEncoder();
const decoder = new TextDecoder("utf-8", { ignoreBOM: true });
const MAX_ROWS = 100;
const MAX_COLUMNS = 16;
const MAX_RESULT_BYTES = 24 * 1024;
const allowedFunctions = new Set(
  "abs avg char coalesce concat concat_ws count dense_rank format glob hex if iif ifnull instr lag lead length like lower ltrim max min mod nullif octet_length pow power printf quote rank replace round row_number rtrim sign substr substring sum total trim typeof unicode upper".split(
    " ",
  ),
);

class QueryError extends Error {
  constructor(
    message: string,
    readonly verdict = "Runtime Error",
  ) {
    super(message);
  }
}

const identifier = (value: string) => `"${value.replaceAll('"', '""')}"`;

export function evaluateQuery(
  sqlite: Sqlite3Static,
  sql: SqlProblem,
  data: SqlCell[][][],
  code: string,
): SqlResultTable {
  const { capi, wasm } = sqlite;
  if (encoder.encode(code).length > 16384 || code.includes("\0"))
    throw new QueryError(
      "SQLは16 KB以内で、NUL文字を含めずに入力してください。",
      "Syntax Error",
    );
  const db = new sqlite.oo1.DB(":memory:", "c");
  const scope = wasm.scopedAllocPush();
  try {
    sql.tables.forEach((table, i) => {
      const name = identifier(table.name);
      const columns = table.columns.map(
        (column) => `${identifier(column.name)} ${column.type}`,
      );
      db.exec(`CREATE TABLE ${name} (${columns.join(", ")})`);
      const marks = columns.map(() => "?");
      const insert = db.prepare(
        `INSERT INTO ${name} VALUES (${marks.join(", ")})`,
      );
      try {
        data[i].forEach((row) => insert.bind(row).stepReset());
      } finally {
        insert.finalize();
      }
    });
    db.exec(
      "PRAGMA query_only=ON; PRAGMA temp_store=MEMORY; PRAGMA trusted_schema=OFF; PRAGMA hard_heap_limit=16777216;",
    );
    const ptr = db.pointer!;
    capi.sqlite3_limit(ptr, capi.SQLITE_LIMIT_LENGTH, 16 * 1024);
    capi.sqlite3_limit(ptr, capi.SQLITE_LIMIT_COLUMN, MAX_COLUMNS);
    capi.sqlite3_limit(ptr, capi.SQLITE_LIMIT_SQL_LENGTH, 16384);
    capi.sqlite3_limit(ptr, capi.SQLITE_LIMIT_ATTACHED, 0);
    let denied = false;
    const tables = new Set(sql.tables.map((table) => table.name));
    const auth = capi.sqlite3_set_authorizer(
      ptr,
      (_ctx, action, arg1, arg2) => {
        if (
          action === capi.SQLITE_SELECT ||
          action === capi.SQLITE_RECURSIVE ||
          (action === capi.SQLITE_READ &&
            typeof arg1 === "string" &&
            tables.has(arg1)) ||
          (action === capi.SQLITE_FUNCTION &&
            typeof arg2 === "string" &&
            allowedFunctions.has(arg2.toLowerCase()))
        )
          return capi.SQLITE_OK;
        denied = true;
        return capi.SQLITE_DENY;
      },
      0,
    );
    if (auth !== capi.SQLITE_OK)
      throw new QueryError("SQLiteの読み取り制限を設定できませんでした。");

    const deadline = performance.now() + 1000;
    capi.sqlite3_progress_handler(
      ptr,
      1000,
      () => Number(performance.now() >= deadline),
      0,
    );
    const check = (rc: number, syntax = false) => {
      if (rc === capi.SQLITE_OK) return;
      if (denied)
        throw new QueryError(
          "演習のテーブルに対する読み取り専用のクエリを1文入力してください。変更や演習外の関数は使えません。",
        );
      if (rc === capi.SQLITE_INTERRUPT)
        throw new QueryError(
          "1秒以内に終わるよう、結合や絞り込みの条件を確認してください。",
          "Time Limit Exceeded",
        );
      if (rc === capi.SQLITE_TOOBIG)
        throw new QueryError(
          "1行のデータが大きすぎます。取り出す値や列を絞ってください。",
        );
      throw new QueryError(
        capi.sqlite3_errmsg(ptr),
        syntax ? "Syntax Error" : "Runtime Error",
      );
    };

    const [stmtOut, tailOut] = wasm.scopedAllocPtr(2);
    const source = wasm.scopedAllocCString(code, false);
    const prepare = (start: number) => {
      check(
        capi.sqlite3_prepare_v3(
          ptr,
          start,
          -1,
          capi.SQLITE_PREPARE_NO_VTAB,
          stmtOut,
          tailOut,
        ),
        true,
      );
      return wasm.peekPtr(stmtOut);
    };
    const stmt = prepare(source);
    if (!stmt)
      throw new QueryError("SELECTクエリを入力してください。", "Syntax Error");
    try {
      // SQLite parses the remaining input too. A trailing comment or semicolon
      // is fine, including when the first statement contains quoted semicolons.
      const tail = prepare(wasm.peekPtr(tailOut));
      if (tail) {
        capi.sqlite3_finalize(tail);
        throw new QueryError(
          "実行できるクエリは1文です。セミコロンで区切った複数文は実行できません。",
          "Syntax Error",
        );
      }
      const count = capi.sqlite3_column_count(stmt);
      if (!count || !capi.sqlite3_stmt_readonly(stmt))
        throw new QueryError(
          "演習では結果を返す読み取り専用のクエリを使います。",
        );
      const columns = Array.from({ length: count }, (_, i) =>
        capi.sqlite3_column_name(stmt, i),
      );
      const rows: SqlCell[][] = [];
      let bytes = encoder.encode(JSON.stringify(columns)).length;
      let rc = capi.sqlite3_step(stmt);
      while (rc === capi.SQLITE_ROW) {
        if (rows.length >= MAX_ROWS)
          throw new QueryError(
            `結果の上限は${MAX_ROWS}行です。WHEREやLIMITで行数を減らしてください。`,
          );
        const row = columns.map((_, i): SqlCell => {
          const type = capi.sqlite3_column_type(stmt, i);
          if (type === capi.SQLITE_NULL) return null;
          if (type === capi.SQLITE_TEXT) {
            const offset = capi.sqlite3_column_blob(stmt, i);
            return decoder.decode(
              wasm
                .heap8u()
                .subarray(offset, offset + capi.sqlite3_column_bytes(stmt, i)),
            );
          }
          if (type === capi.SQLITE_INTEGER) {
            const n = Number(capi.sqlite3_column_int64(stmt, i));
            if (Number.isSafeInteger(n)) return n;
          }
          if (type === capi.SQLITE_FLOAT) {
            const n = capi.sqlite3_column_double(stmt, i);
            if (Number.isFinite(n)) return n;
          }
          throw new QueryError(
            "結果は表示可能な数値・文字列・NULLにしてください。",
          );
        });
        bytes += encoder.encode(JSON.stringify(row)).length + 1;
        if (bytes > MAX_RESULT_BYTES)
          throw new QueryError(
            "結果が大きすぎます。取り出す行や列を絞ってください。",
          );
        rows.push(row);
        rc = capi.sqlite3_step(stmt);
      }
      if (rc !== capi.SQLITE_DONE) check(rc);
      return { columns, rows };
    } finally {
      capi.sqlite3_finalize(stmt);
    }
  } finally {
    wasm.scopedAllocPop(scope);
    db.close();
  }
}

export function sameTable(
  actual: SqlResultTable,
  expected: SqlResultTable,
  options: Pick<SqlProblem, "ordered" | "column_names" | "approximate">,
  tolerance: number,
) {
  if (
    actual.columns.length !== expected.columns.length ||
    actual.rows.length !== expected.rows.length
  )
    return false;
  if (
    options.column_names &&
    actual.columns.some((name, i) => name !== expected.columns[i])
  )
    return false;
  const sameRow = (a: SqlCell[], b: SqlCell[]) =>
    a.length === b.length &&
    a.every((value, i) => {
      const other = b[i];
      return (
        value === other ||
        (options.approximate &&
          typeof value === "number" &&
          typeof other === "number" &&
          Math.abs(value - other) <=
            tolerance * Math.max(1, Math.abs(value), Math.abs(other)))
      );
    });
  if (options.ordered)
    return actual.rows.every((row, i) => sameRow(row, expected.rows[i]));
  // Match each expected row once. When tolerance creates overlapping matches,
  // let a row move to another matching slot before declaring a mismatch.
  const assigned = expected.rows.map(() => -1);
  const match = (i: number, seen: Set<number>): boolean =>
    expected.rows.some((row, j) => {
      if (seen.has(j) || !sameRow(actual.rows[i], row)) return false;
      seen.add(j);
      if (assigned[j] !== -1 && !match(assigned[j], seen)) return false;
      assigned[j] = i;
      return true;
    });
  return actual.rows.every((_, i) => match(i, new Set()));
}

export function runSql(
  sqlite: Sqlite3Static,
  sql: SqlProblem,
  code: string,
  preview: boolean,
  tolerance: number,
): Result {
  const started = performance.now();
  const cases = preview ? sql.cases.slice(0, 1) : sql.cases;
  let failure: QueryError | undefined;
  const tests = cases.map(({ rows, expected }, i) => {
    const name = `入力例 ${i + 1}`;
    try {
      const actual = evaluateQuery(sqlite, sql, rows, code);
      return {
        name,
        actual,
        passed: preview || sameTable(actual, expected, sql, tolerance),
      };
    } catch (error) {
      failure ??=
        error instanceof QueryError
          ? error
          : new QueryError(
              "SQLiteの実行に失敗しました。もう一度お試しください。",
            );
      return { name, passed: false, error: failure.message.slice(0, 500) };
    }
  });
  const passed = tests.filter((test) => test.passed).length;
  return {
    verdict:
      failure?.verdict ??
      (passed === cases.length ? "Accepted" : "Wrong Answer"),
    stderr: failure?.message.slice(0, 500),
    passed_tests: passed,
    total_tests: cases.length,
    elapsed_ms: performance.now() - started,
    tests,
    preview,
  };
}
