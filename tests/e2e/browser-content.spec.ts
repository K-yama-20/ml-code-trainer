import { test, expect } from "./qa-fixture";
import { readFile, writeFile, mkdir } from "node:fs/promises";
test("all browser problem references pass in the production Pyodide runner", async ({
  page,
}) => {
  test.skip(
    process.env.RUN_BROWSER_CONTENT !== "1",
    "Full Pyodide suite: run npm run test:browser-content",
  );
  test.setTimeout(1200000);
  const catalog = JSON.parse(
    await readFile("content/compiled/private.json", "utf8"),
  );
  await page.goto("/home");
  await expect(
    page.getByRole("heading", { name: "今日も、コードを読む力を。" }),
  ).toBeVisible();
  const results = [];
  // Optional scope for content work, e.g. BROWSER_CONTENT_CONCEPTS=NP09,PD01
  const scope = (process.env.BROWSER_CONTENT_CONCEPTS ?? "")
    .split(",")
    .filter(Boolean);
  const problems = catalog.problems.filter(
    (p: { runtime: string; concept_id: string }) =>
      p.runtime === "browser" &&
      (!scope.length || scope.includes(p.concept_id)),
  );
  for (const p of problems) {
    const result = await page.evaluate(async (p) => {
      // Test-only injection; private content never enters the shipped web bundle.
      const runner = await import("/src/features/python.ts");
      return runner.browserRun(
        { ...p, public_tests: [...p.public_tests, ...p.hidden_tests] },
        p.solution,
        () => {},
        new AbortController().signal,
      );
    }, p);
    results.push({
      id: p.id,
      verdict: result.verdict,
      passed: result.passed_tests,
      total: result.total_tests,
      error: result.stderr,
    });
    if (results.length % 10 === 0)
      console.log(`Pyodide content: ${results.length}/${problems.length}`);
  }
  await mkdir("artifacts", { recursive: true });
  await writeFile(
    "artifacts/browser-content-validation.json",
    JSON.stringify(results, null, 2),
  );
  expect(results.filter((r) => r.verdict !== "Accepted")).toEqual([]);
  expect(results).toHaveLength(problems.length);
});
