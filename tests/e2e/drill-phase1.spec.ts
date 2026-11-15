import { test, expect, type Page } from "./qa-fixture";
import { readFileSync, writeFileSync } from "node:fs";
import type { Problem, StudySession } from "../../apps/web/src/types/domain";
type Authored = Problem & { solution: string };
// Every drill problem is an ordered `result = <expression>` exercise written in
// the unified Monaco document; the authored order lives in the compiled catalog.
const authored = JSON.parse(
  readFileSync("content/compiled/private.json", "utf-8"),
).problems as Authored[];
const byId = (id: string) => authored.find((p) => p.id === id)!;
const NP05 = authored.filter((p) => p.concept_id === "NP05");
async function session(page: Page, id = "NP05-01", kind = "custom") {
  await page.goto("/home");
  await expect(
    page.getByRole("button", { name: "学習を再開", exact: true }),
  ).toBeVisible();
  const r = await page.request.post("/api/v1/sessions", {
    data: { kind, concept_id: id.split("-")[0], count: 20 },
  });
  expect(r.ok()).toBeTruthy();
  const s = (await r.json()) as StudySession;
  const item = s.items.find((i) => i.problem_version_id.startsWith(id + "@"))!;
  await page.goto(`/drill/s/${s.id}/${item.id}`);
  await expect(page.locator(".problem-content h1")).toBeVisible();
  return { s, item };
}
const lines = (page: Page) => page.locator(".view-lines");
async function code(page: Page, value: string) {
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  await expect(editor).toBeVisible();
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate((s) => navigator.clipboard.writeText(s), value);
  await editor.press("ControlOrMeta+A");
  await editor.press("ControlOrMeta+V");
}
async function solve(page: Page, p: Authored) {
  await code(page, p.solution);
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({ timeout: 150000 });
  await expect(page.locator(".verdict.accepted")).toContainText("正解です");
}
async function currentProblem(page: Page) {
  const ids = new URL(page.url()).pathname.split("/");
  const detail = await (
    await page.request.get(`/api/v1/sessions/${ids.at(-2)}/items/${ids.at(-1)}`)
  ).json();
  return {
    itemId: ids.at(-1)!,
    p: authored.find((x) => x.version_id === detail.problem.version_id)!,
  };
}
test("21 real answers follow the authored order, move to the next concept and pass the 20-question goal", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const { s } = await session(page, NP05[0].id, "concept");
  const sequence: { id: string; stage: string }[] = [];
  await expect(page.locator(".learning-goal")).toHaveCount(0);
  await expect(page.getByText("公開テスト", { exact: true })).toHaveCount(0);
  await expect(page.getByText("よくある間違い", { exact: true })).toHaveCount(
    0,
  );
  await page.screenshot({
    path: "docs/ux-concrete/after-drill-desktop.png",
    fullPage: true,
  });
  for (let n = 0; n < 21; n++) {
    const { itemId, p } = await currentProblem(page);
    await expect(page.locator(".problem-content h1")).toHaveText(p.title);
    sequence.push({ id: p.id, stage: p.stage });
    await solve(page, p);
    if (n === 0)
      await page.screenshot({
        path: "docs/ux-concrete/after-correct.png",
        fullPage: true,
      });
    await page.getByRole("button", { name: "次の問題", exact: true }).click();
    await expect(page).not.toHaveURL(/\/home$/);
    await expect(page).not.toHaveURL(new RegExp(itemId));
    await expect(page.locator(".problem-content h1")).toBeVisible();
  }
  expect(sequence.slice(0, 18).map((p) => p.id)).toEqual(
    NP05.map((p) => p.id),
  );
  expect(sequence.slice(18).every((p) => !p.id.startsWith("NP05"))).toBe(true);
  const current = await (
    await page.request.get("/api/v1/sessions/current")
  ).json();
  expect(current.id).toBe(s.id);
  expect(current.status).toBe("active");
  expect(current.position).toBe(21);
  expect(current.goal_count).toBe(20);
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    21,
  );
  // Independent answers ran in the browser, so they stay provisional.
  expect(
    (await (await page.request.get("/api/v1/progress/concepts")).json()).find(
      (p: { concept_id: string }) => p.concept_id === "NP05",
    ).mastery_level,
  ).toBe(2);
  await page.screenshot({
    path: "docs/ux-concrete/after-21-answers.png",
    fullPage: true,
  });
  writeFileSync(
    "artifacts/concrete-drill/continuous-21.json",
    JSON.stringify({ sequence, current, errors }, null, 2),
  );
  expect(errors).toEqual([]);
});
test("wrong answers retain code, Run does not submit, the hint is recorded and accepted Submit records it", async ({
  page,
}) => {
  const { item } = await session(page);
  await code(page, "result = np.mean(x, axis=0)");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toContainText("結果が異なります", {
    timeout: 150000,
  });
  await expect(lines(page)).toContainText("np.mean(x, axis=0)");
  // x = [[1, 4, 7], [2, 6, 10]]: column means are shown against row means.
  await expect(page.locator(".value-comparison").first()).toContainText("8.5");
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    0,
  );
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toHaveCount(0);
  await page.screenshot({
    path: "docs/ux-concrete/after-wrong-comparison.png",
    fullPage: true,
  });
  await page.locator(".drill-hints summary").click();
  await expect(page.locator(".drill-hints p")).not.toHaveText("読み込み中…");
  await page.screenshot({
    path: "docs/ux-concrete/after-hints.png",
    fullPage: true,
  });
  await page.locator(".editor-heading .drill-menu summary").click();
  await page
    .getByRole("button", { name: "初期状態に戻す", exact: true })
    .click();
  await expect(lines(page)).not.toContainText("axis=0");
  await page
    .getByRole("button", { name: "変更前の回答を戻す", exact: true })
    .click();
  await expect(lines(page)).toContainText("np.mean(x, axis=0)");
  await solve(page, byId("NP05-01"));
  const history = await (await page.request.get("/api/v1/history")).json();
  expect(history.total).toBe(1);
  expect(history.items[0].hint_level_used).toBe(1);
  expect(history.items[0].submitted_code).toContain("np.mean(x, axis=1)");
  await page.reload();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible();
  await expect(lines(page)).toContainText("np.mean(x, axis=1)");
  expect(
    (await (await page.request.get(`/api/v1/drafts/${item.id}`)).json()).code,
  ).toContain("np.mean(x, axis=1)");
});
test("unavailable runtime is explained before work; empty continuation stays on the drill", async ({
  page,
}) => {
  await session(page, "PT02-02");
  await expect(page.locator(".runtime-unavailable")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "答え合わせ", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "実行のみ", exact: true }),
  ).toBeDisabled();
  await page.screenshot({
    path: "docs/ux-concrete/after-unavailable.png",
    fullPage: true,
  });
  // Choose a one-stage custom queue so only two unavailable items precede depletion.
  const r = await page.request.post("/api/v1/sessions", {
    data: { kind: "custom", concept_id: "PT02", stages: ["guided"], count: 2 },
  });
  const s = await r.json();
  await page.goto(`/drill/s/${s.id}/${s.items[0].id}`);
  for (let n = 0; n < 2; n++) {
    await page.locator(".drill-top .drill-menu summary").click();
    await page
      .getByRole("button", { name: "この問題は後で", exact: true })
      .click();
    if (n === 0) await expect(page).toHaveURL(new RegExp(s.items[1].id));
  }
  await expect(page.locator(".no-next")).toContainText(
    "実行できる問題がありません",
  );
  await expect(page).not.toHaveURL(/\/home$/);
});
test("mobile and tablet keep one primary action and preserve the answer", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await session(page);
  await page.screenshot({
    path: "docs/ux-concrete/after-mobile-question.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "回答欄へ", exact: true }).click();
  await code(page, byId("NP05-01").solution);
  await page.screenshot({
    path: "docs/ux-concrete/after-mobile-editor.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({ timeout: 150000 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  const box = await page
    .getByRole("button", { name: "次の問題", exact: true })
    .boundingBox();
  expect(box!.y + box!.height).toBeLessThanOrEqual(844);
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.screenshot({
    path: "docs/ux-concrete/after-tablet.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
test("cancel is explicit and never displays a completed result for the cancelled run", async ({
  page,
}) => {
  await session(page);
  await solve(page, byId("NP05-01"));
  await code(page, 'result = exec("while True: pass")');
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await page.getByRole("button", { name: "中止", exact: true }).click();
  await expect(page.locator(".execution-notice")).toContainText("中止");
  await expect(page.locator(".verdict")).toHaveCount(0);
  await expect(lines(page)).toContainText("while True");
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    1,
  );
});

test("starting from the concept page shows no stage labels; ending is explicit", async ({
  page,
}) => {
  await page.goto("/concepts/NP05");
  for (let n = 0; n < 2; n++) {
    await expect(page.locator(".problem-content h1")).toBeVisible();
    const { itemId, p } = await currentProblem(page);
    expect(p.id).toBe(NP05[n].id);
    await solve(page, p);
    await page.getByRole("button", { name: "次の問題", exact: true }).click();
    await expect(page).not.toHaveURL(new RegExp(itemId));
  }
  await expect(page.locator(".problem-content h1")).toBeVisible();
  await expect(
    page.locator(".transition-note, .session-label", {
      hasText: /穴埋め|部分記述|補助なし|Guided|Partial|Independent/,
    }),
  ).toHaveCount(0);
  await page.locator(".drill-top .drill-menu summary").click();
  await page.getByRole("button", { name: "演習を終了", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "今回の演習を終了しました" }),
  ).toBeVisible();
  await page.screenshot({
    path: "docs/ux-concrete/after-ended.png",
    fullPage: true,
  });
  await expect(page).not.toHaveURL(/\/home$/);
  expect(
    await (await page.request.get("/api/v1/sessions/current")).json(),
  ).toBeNull();
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    2,
  );
});
