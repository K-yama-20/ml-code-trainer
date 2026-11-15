import { readFile } from "node:fs/promises";
import { expect, test, type Page } from "./qa-fixture";
import type { SqlProblem } from "../../apps/web/src/types/domain";

test.use({ actionTimeout: 10000 });
test.setTimeout(45000);

async function writeSql(page: Page, code: string) {
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  await editor.press("ControlOrMeta+A");
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate((text) => navigator.clipboard.writeText(text), code);
  await editor.press("ControlOrMeta+V");
  await expect(page.locator(".view-lines")).toContainText(code);
  return editor;
}

test("SQLite drill runs and submits, then preserves drafts and results across navigation", async ({
  page,
}) => {
  await page.goto("/curriculum/sql");
  await expect(page.getByText("29問のDrill")).toBeVisible();
  await page.getByRole("link", { name: /SQL01.*表を見る/ }).click();
  await expect(
    page.getByRole("table", { name: "sales のサンプル" }),
  ).toBeVisible();
  await expect(page.getByText("query.sql")).toBeVisible();
  await writeSql(page, "SELECT id FROM sales;");
  await page.getByRole("button", { name: "実行のみ" }).click();
  const table = page.getByRole("table", { name: "実行結果", exact: true });
  await expect(table.getByRole("columnheader", { name: "id" })).toBeVisible();
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    0,
  );
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByText("結果が異なります", { exact: true }),
  ).toBeVisible();
  await page.getByText("入力例 1 · 結果を比較", { exact: true }).click();
  await expect(
    page.getByRole("table", { name: "入力例 1 の期待する結果" }),
  ).toBeVisible();

  const code = "SELECT * FROM sales; -- 保存される回答";
  const editor = await writeSql(page, code);
  await editor.press("ControlOrMeta+Enter");
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("ブラウザで答え合わせ・暫定")).toHaveCount(0);
  await expect(table.getByRole("columnheader", { name: "note" })).toBeVisible();
  await expect(
    table.getByRole("cell", { name: "NULL", exact: true }).first(),
  ).toBeVisible();
  await expect(
    table.getByRole("cell", { name: "''", exact: true }),
  ).toBeVisible();
  const url = page.url();
  await page.getByRole("button", { name: "次の問題", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "商品名だけを取り出す" }),
  ).toBeVisible();
  await page.goto(url);
  await expect(page.locator(".view-lines")).toContainText(code);
  await expect(table.getByRole("columnheader", { name: "note" })).toBeVisible();
  await page.goto("/curriculum/sql");
  await expect(page.getByText("練習 1/3問正解")).toBeVisible();
});

test("mobile SQL keeps the query when switching views, scrolling results, and stopping", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/curriculum/sql");
  await page.getByRole("link", { name: /SQL07.*テーブルの結合/ }).click();
  await page
    .locator(".problem-pane summary")
    .filter({ hasText: "purchases" })
    .click();
  await expect(
    page.getByRole("table", { name: "purchases のサンプル" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "回答欄へ" }).click();
  const code =
    "SELECT name AS long_customer_name_column, name AS another_customer_name_column FROM customers";
  await writeSql(page, code);
  await page.getByRole("tab", { name: "問題", exact: true }).click();
  await page.getByRole("tab", { name: "回答・結果", exact: true }).click();
  await expect(page.locator(".view-lines")).toContainText(code);
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  const result = page.getByRole("region", { name: "実行結果", exact: true });
  await expect(result).toBeVisible();
  expect(
    await result.evaluate((view) => {
      view.scrollLeft = view.scrollWidth;
      return view.scrollLeft;
    }),
  ).toBeGreaterThan(0);

  const long =
    "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT sum(x) FROM n";
  await writeSql(page, long);
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await page.getByRole("button", { name: "中止", exact: true }).click();
  await expect(
    page.getByText("今回の実行を中止しました。回答は保持されています。"),
  ).toBeVisible();
  await expect(page.locator(".view-lines")).toContainText(long);
  await writeSql(page, "SELECT name FROM customers");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(
    result.getByRole("columnheader", { name: "name" }),
  ).toBeVisible();
});

test("both course variants execute all references in the SQLite browser runtime", async ({
  page,
}) => {
  const all: {
    id: string;
    variant_seed: number;
    solution: string;
    sql?: SqlProblem;
    hidden_tests: SqlProblem["cases"];
  }[] = [];
  for (const catalog of ["private", "variant-99"])
    all.push(
      ...JSON.parse(
        await readFile(`content/compiled/${catalog}.json`, "utf8"),
      ).problems.filter((p: { sql?: SqlProblem }) => p.sql),
    );
  expect(all.length).toBe(58);
  await page.goto("/");
  const results = await page.evaluate(async (problems) => {
    // Test-only injection, like the Pyodide reference checks.
    const { browserSql } = await import("/src/features/sql-runtime.ts");
    const signal = new AbortController().signal;
    const errors = [];
    for (const p of problems) {
      const sql = p.sql!;
      const result = await browserSql(
        { ...sql, cases: [...sql.cases, ...p.hidden_tests] },
        p.solution,
        false,
        1e-8,
        () => {},
        signal,
      );
      if (result.verdict !== "Accepted")
        errors.push({ id: p.id, seed: p.variant_seed, result });
    }
    return errors;
  }, all);
  expect(results).toEqual([]);
});

test("SQLite rejects disallowed statements and bounds execution and output", async ({
  page,
}) => {
  await page.goto("/");
  const { sql } = await (
    await page.request.get("/api/v1/problems/SQL01-01")
  ).json();
  const results = await page.evaluate(async (sql) => {
    const { browserSql } = await import("/src/features/sql-runtime.ts");
    const codes = [
      "SELECT 'a;b' AS value; /* comment ; */",
      "SELECT 1; SELECT 2;",
      "UPDATE sales SET amount=0 RETURNING amount;",
      "PRAGMA query_only=OFF;",
      "ATTACH ':memory:' AS other;",
      "SELEC id FROM sales;",
      "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<101) SELECT x FROM n;",
      "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT sum(x) FROM n;",
      "SELECT * FROM sales;",
    ];
    const results = [];
    for (const code of codes)
      results.push(
        await browserSql(
          sql,
          code,
          true,
          1e-8,
          () => {},
          new AbortController().signal,
        ),
      );
    return results;
  }, sql);
  expect(results.map((r) => r.verdict)).toEqual([
    "Accepted",
    "Syntax Error",
    "Runtime Error",
    "Runtime Error",
    "Runtime Error",
    "Syntax Error",
    "Runtime Error",
    "Time Limit Exceeded",
    "Accepted",
  ]);
  expect(results[6].stderr).toContain("100行");
  expect(results[8].tests?.[0].actual).toEqual(sql.cases[0].expected);
});
