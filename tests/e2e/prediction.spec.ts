import { test, expect } from "./qa-fixture";
import { readFileSync, mkdirSync } from "node:fs";
const all = JSON.parse(
  readFileSync("content/compiled/private.json", "utf-8"),
).problems;
mkdirSync("docs/ux-concrete", { recursive: true });

function pythonValue(value: unknown): string {
  if (value === null) return "None";
  if (typeof value === "boolean") return value ? "True" : "False";
  if (Array.isArray(value)) return `[${value.map(pythonValue).join(", ")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .map(([k, v]) => `${JSON.stringify(k)}: ${pythonValue(v)}`)
      .join(", ")}}`;
  return JSON.stringify(value);
}
for (const p of all.filter((p: { type: string }) => p.type === "prediction"))
  test(`prediction answer ${p.id}: values entered in the field are accepted and saved`, async ({
    page,
  }) => {
    await page.goto("/home");
    await expect(
      page.getByRole("button", { name: "学習を再開", exact: true }),
    ).toBeVisible();
    const s = await (
      await page.request.post("/api/v1/sessions", {
        data: { kind: "custom", concept_id: p.concept_id, count: 6 },
      })
    ).json();
    const item = s.items.find(
      (i: { problem_version_id: string }) =>
        i.problem_version_id === p.version_id,
    );
    await page.goto(`/drill/s/${s.id}/${item.id}`);
    const value = p.presentation.answer.wrap_array
      ? p.public_tests[0].expected.data
      : p.public_tests[0].expected;
    await page.locator("#prediction-value").fill(pythonValue(value));
    await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "次の問題", exact: true }),
    ).toBeVisible({ timeout: 150000 });
    await expect(page.locator(".submission-note")).toContainText("履歴に保存");
    if (p.id === "NP01-04")
      await page.screenshot({
        path: "docs/ux-concrete/after-prediction-dtype.png",
        fullPage: true,
      });
  });
