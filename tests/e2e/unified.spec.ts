import { test, expect, type Page } from "./qa-fixture";
import { drillItem } from "./drill-helpers";
import { readFileSync } from "node:fs";
const ps = JSON.parse(
  readFileSync("content/compiled/private.json", "utf8"),
).problems;
async function open(page: Page, id = "PY01-03@3") {
  return (await drillItem(page, id)).item;
}
async function write(page: any, s: string) {
  const e = page.getByRole("textbox", { name: "Editor content", exact: true });
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate((s: string) => navigator.clipboard.writeText(s), s);
  await e.press("ControlOrMeta+A");
  await e.press("ControlOrMeta+V");
}
test("zip: protection, undo/redo, disclosure, grading, draft and screenshots", async ({
  page,
}) => {
  const item = await open(page);
  await page.screenshot({ path: "docs/ux-unified/zip-dark-before.png" });
  const hint = page.locator(".drill-hints"),
    solution = page.locator(".solution-accordion");
  await expect(hint).not.toHaveAttribute("open", "");
  await expect(solution).not.toHaveAttribute("open", "");
  await write(page, "result = dict(zip(keys, values))\n");
  const e = page.getByRole("textbox", { name: "Editor content", exact: true });
  await e.press("ControlOrMeta+Home");
  await e.press("Delete");
  await expect(page.locator(".view-lines")).toContainText("keys = ['a', 'b']");
  await e.press("ControlOrMeta+Home");
  await e.press("Backspace");
  await expect(page.locator(".view-lines")).toContainText("values = [2, 3]");
  await e.press("ControlOrMeta+Home");
  await e.press("ControlOrMeta+Shift+End");
  await page.evaluate(() =>
    navigator.clipboard.writeText("changed fixed code"),
  );
  await e.press("ControlOrMeta+V");
  await expect(page.locator(".view-lines")).toContainText("values = [2, 3]");
  await expect(page.locator(".view-lines")).toContainText("result = dict(zip");
  await hint.locator("summary").click();
  await expect(hint).toContainText("dict()");
  await hint.locator("summary").click();
  await expect(hint).not.toHaveAttribute("open", "");
  await solution.locator("summary").click();
  await expect(solution.locator("pre")).toContainText("dict(zip");
  await solution.locator("summary").click();
  await expect(solution.locator("pre")).not.toBeVisible();
  await expect(page.locator(".view-lines")).toContainText("result = dict(zip");
  const detail = await (
    await page.request.get(
      `/api/v1/sessions/${item.session_id}/items/${item.id}`,
    )
  ).json();
  expect(detail.solution_viewed).toBe(true);
  expect(detail.hint_level).toBeGreaterThan(0);
  await write(page, "result = {}\n");
  await e.press("ControlOrMeta+z");
  await expect(page.locator(".view-lines")).toContainText("dict(zip");
  await e.press("ControlOrMeta+y");
  await expect(page.locator(".view-lines")).toContainText("result = {}");
  await write(page, "result = dict(zip(keys, values))\n");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({ timeout: 150000 });
  await page.screenshot({ path: "docs/ux-unified/zip-dark-correct.png" });
  await page.reload();
  await expect(page.locator(".view-lines")).toContainText("result = dict(zip");
  await page.goto("/settings");
  await page.getByLabel("テーマ", { exact: true }).selectOption("light");
  await page.getByRole("button", { name: "変更を保存", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("設定を保存");
  await page.goto(`/drill/s/${item.session_id}/${item.id}`);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator(".problem-content h1")).toBeVisible();
  await expect(page.locator(".monaco-editor")).toBeVisible();
  await page.screenshot({ path: "docs/ux-unified/zip-light-correct.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("tab", { name: "回答・結果", exact: true }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: "docs/ux-unified/mobile.png" });
});
for (const id of ["NP05-01", "NP05-05", "PY02-06", "PT05-03", "PT02-02"])
  test("unified structure " + id, async ({ page }) => {
    await open(page, id);
    await expect(page.locator(".provided-input")).toHaveCount(0);
    await expect(page.locator(".editor-guide")).toHaveCount(0);
    await page.screenshot({ path: `docs/ux-unified/${id}.png` });
  });

test("21 submissions continue through all stages without going home", async ({
  page,
}) => {
  await page.goto("/home");
  await expect(
    page.getByRole("button", { name: "学習を再開", exact: true }),
  ).toBeVisible();
  const s = await (
    await page.request.post("/api/v1/sessions", {
      data: { kind: "daily", concept_id: "NP05", count: 20 },
    })
  ).json();
  await page.goto(`/drill/s/${s.id}/${s.items[0].id}`);
  for (let n = 0; n < 21; n++) {
    await expect(page.locator(".problem-content h1")).toBeVisible();
    const ids = new URL(page.url()).pathname.split("/");
    const item = await (
      await page.request.get(`/api/v1/sessions/${s.id}/items/${ids.at(-1)}`)
    ).json();
    const p = ps.find((p: any) => p.version_id === item.problem.version_id);
    if (p.type === "prediction") {
      const value = p.presentation.answer.wrap_array
        ? p.public_tests[0].expected.data
        : p.public_tests[0].expected;
      await page.locator("#prediction-value").fill(JSON.stringify(value));
    } else {
      let text = p.solution;
      if (p.editable_regions.length) {
        text = text.slice(p.editable_regions[0].start);
      } else if (
        p.type !== "bugfix" &&
        p.starter_code.split("___").length === 2
      ) {
        const [a, b] = p.starter_code.split("___");
        text = text.slice(a.length, b ? -b.length : undefined);
      }
      if (p.starter_code.match(/^def /) && p.starter_code.includes("pass")) {
        text = p.solution
          .slice(p.solution.indexOf("\n") + 1)
          .replace(/^\n+/, "");
        text = text.slice(4);
      }
      await write(page, text);
    }
    await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "次の問題", exact: true }),
      `Question ${n + 1}: ${p.id}`,
    ).toBeVisible({ timeout: 150000 });
    await page.getByRole("button", { name: "次の問題", exact: true }).click();
    await expect(page).not.toHaveURL(/home$/);
    await expect(page).not.toHaveURL(new RegExp(ids.at(-1)!));
  }
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    21,
  );
  await page.screenshot({ path: "docs/ux-unified/after-21.png" });
});
