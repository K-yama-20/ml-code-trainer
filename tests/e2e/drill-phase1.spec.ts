import { test, expect, type Page } from "./qa-fixture";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import type { Problem, StudySession } from "../../apps/web/src/types/domain";
type Authored = Problem & { solution: string };
const authored = JSON.parse(
  readFileSync("content/compiled/private.json", "utf-8"),
).problems as Authored[];
mkdirSync("docs/ux-phase1", { recursive: true });
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
async function code(page: Page, value: string) {
  const blank = page.getByRole("textbox", {
    name: "コードの空欄",
    exact: true,
  });
  if (await blank.count()) {
    const ids = new URL(page.url()).pathname.split("/");
    const detail = await (
      await page.request.get(
        `/api/v1/sessions/${ids.at(-2)}/items/${ids.at(-1)}`,
      )
    ).json();
    const [prefix, suffix] = detail.problem.starter_code.split("___");
    const source = value.startsWith("def solve(")
      ? value
          .split("\n")
          .slice(1)
          .map((s) => s.slice(4))
          .join("\n")
          .replace("return ", "result = ")
      : value;
    if (source.includes("while True"))
      await blank.fill("exec('while True: pass')");
    else {
      expect(source.startsWith(prefix) && source.endsWith(suffix)).toBeTruthy();
      await blank.fill(
        source.slice(prefix.length, suffix ? -suffix.length : undefined),
      );
    }
    return;
  }
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  await expect(editor).toBeVisible();
  await editor.press("ControlOrMeta+A");
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate((s) => navigator.clipboard.writeText(s), value);
  await editor.press("ControlOrMeta+V");
}
function literal(v: unknown): string {
  if (v === null) return "None";
  if (typeof v === "boolean") return v ? "True" : "False";
  if (Array.isArray(v)) return `[${v.map(literal).join(", ")}]`;
  if (v && typeof v === "object")
    return `{${Object.entries(v)
      .map(([k, x]) => JSON.stringify(k) + ": " + literal(x))
      .join(", ")}}`;
  return JSON.stringify(v);
}
async function solve(page: Page, p: Authored) {
  if (p.type === "prediction") {
    const expected = p.public_tests[0].expected as {
      kind?: string;
      data?: unknown;
    };
    const value =
      p.presentation?.answer?.mode === "fixed"
        ? literal(p.presentation.answer.wrap_array ? expected.data : expected)
        : p.solution.split("return ").at(-1)!.trim();
    await page.locator("#prediction-value").fill(value);
  } else await code(page, p.solution);
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({ timeout: 150000 });
  await expect(page.locator(".submission-note")).toContainText("履歴に保存");
}
test("21 real answers continue past Guided, Partial, Independent and the 20-question goal", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const { s } = await session(page, "NP05-01", "daily");
  const sequence = [];
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
    const ids = new URL(page.url()).pathname.split("/");
    const sid = ids.at(-2)!;
    const itemid = ids.at(-1)!;
    const detail = await (
      await page.request.get(`/api/v1/sessions/${sid}/items/${itemid}`)
    ).json();
    const p = authored.find((x) => x.version_id === detail.problem.version_id)!;
    await expect(page.locator(".problem-content h1")).toHaveText(p.title);
    if (p.type === "prediction")
      await expect(page.locator("#prediction-value")).toBeVisible();
    else
      await expect(
        page.getByRole("textbox", { name: /^(Editor content|コードの空欄)$/ }),
      ).toBeVisible();
    sequence.push({ id: p.id, stage: p.stage, type: p.type });
    if (n === 3)
      await page.screenshot({
        path: "docs/ux-concrete/after-prediction-expression.png",
        fullPage: true,
      });
    await solve(page, p);
    if (n === 0)
      await page.screenshot({
        path: "docs/ux-concrete/after-correct.png",
        fullPage: true,
      });
    await page.getByRole("button", { name: "次の問題", exact: true }).click();
    await expect(page).not.toHaveURL(/\/home$/);
    await expect(page).not.toHaveURL(new RegExp(itemid));
    await expect(page.locator(".problem-content h1")).toBeVisible();
    if (n === 1)
      await page.screenshot({
        path: "docs/ux-concrete/after-guided-to-partial.png",
        fullPage: true,
      });
  }
  expect(sequence.slice(0, 6).map((p) => p.stage)).toEqual([
    "guided",
    "guided",
    "partial",
    "partial",
    "independent",
    "independent",
  ]);
  expect(sequence[6].id.startsWith("NP05")).toBe(false);
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
test("wrong answers retain code, Run does not submit, hints are incremental and accepted Submit records them", async ({
  page,
}) => {
  const { item } = await session(page);
  const wrong = "result = x.mean(axis=0)\n";
  await code(page, wrong);
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toContainText("結果が異なります", {
    timeout: 150000,
  });
  await expect(page.getByRole("textbox", { name: "コードの空欄" })).toHaveValue(
    "0",
  );
  await expect(page.locator(".value-comparison").first()).toContainText(
    "3.333",
  );
  await expect(page.locator(".value-comparison").first()).toContainText("1.5");
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
  for (let n = 1; n <= 3; n++) {
    await page
      .getByRole("button", {
        name: n === 1 ? "ヒントを1つ見る" : "次のヒントを見る",
        exact: true,
      })
      .click();
    await expect(page.locator(".hint-step")).toHaveCount(n);
  }
  await page.screenshot({
    path: "docs/ux-concrete/after-hints.png",
    fullPage: true,
  });
  await page.locator(".editor-heading .drill-menu summary").click();
  await page
    .getByRole("button", { name: "初期状態に戻す", exact: true })
    .click();
  await expect(page.getByRole("textbox", { name: "コードの空欄" })).toHaveValue(
    "",
  );
  await page
    .getByRole("button", { name: "変更前の回答を戻す", exact: true })
    .click();
  await expect(page.getByRole("textbox", { name: "コードの空欄" })).toHaveValue(
    "0",
  );
  await solve(
    page,
    authored.find((p) => p.id === "NP05-01")!,
  );
  const history = await (await page.request.get("/api/v1/history")).json();
  expect(history.total).toBe(1);
  expect(history.items[0].hint_level_used).toBe(3);
  expect(history.items[0].submitted_code).toContain("x.mean(axis=1)");
  await page.reload();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("textbox", { name: "コードの空欄" })).toHaveValue(
    "1",
  );
  expect(
    (await (await page.request.get(`/api/v1/drafts/${item.id}`)).json()).code,
  ).toContain("x.mean(axis=1)");
});
test("fixed predictions use a value field and execute through the existing grading path", async ({
  page,
}) => {
  for (const id of ["NP06-04", "PY03-04"]) {
    await session(page, id);
    await expect(page.locator("#prediction-value")).toBeVisible();
    await expect(page.locator(".monaco-editor")).toHaveCount(0);
    await page.locator("#prediction-value").fill("0");
    await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
    await expect(page.locator(".verdict")).toContainText("結果が異なります", {
      timeout: 150000,
    });
    await expect(page.locator("#prediction-value")).toHaveValue("0");
    await solve(
      page,
      authored.find((p) => p.id === id)!,
    );
    await page.screenshot({
      path: `docs/ux-concrete/after-prediction-${id}.png`,
      fullPage: true,
    });
  }
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
  await expect(
    page.getByRole("textbox", { name: "コードの空欄", exact: true }),
  ).toBeVisible();
  await code(page, "def solve(x):\n    return x.mean(axis=1)\n");
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
  await solve(
    page,
    authored.find((p) => p.id === "NP05-01")!,
  );
  await code(page, "def solve(x):\n    while True:\n        pass\n");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await page.getByRole("button", { name: "中止", exact: true }).click();
  await expect(page.locator(".execution-notice")).toContainText("中止");
  await expect(page.locator(".verdict")).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "コードの空欄" })).toHaveValue(
    /while True/,
  );
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    1,
  );
});

test("starting Guided from the concept page continues into Partial; ending is explicit", async ({
  page,
}) => {
  await page.goto("/concepts/NP05");
  await page
    .getByRole("button", { name: "このステージを練習", exact: true })
    .first()
    .click();
  for (let n = 0; n < 2; n++) {
    await expect(page.locator(".problem-content h1")).toBeVisible();
    const ids = new URL(page.url()).pathname.split("/");
    const detail = await (
      await page.request.get(
        `/api/v1/sessions/${ids.at(-2)}/items/${ids.at(-1)}`,
      )
    ).json();
    const p = authored.find((p) => p.version_id === detail.problem.version_id)!;
    expect(p.stage).toBe("guided");
    await solve(page, p);
    await page.getByRole("button", { name: "次の問題", exact: true }).click();
    await expect(page).not.toHaveURL(new RegExp(ids.at(-1)!));
  }
  await expect(page.locator(".transition-note")).toContainText("部分記述");
  await expect(page.locator(".problem-content h1")).toBeVisible();
  await page.screenshot({
    path: "docs/ux-concrete/after-guided-to-partial.png",
    fullPage: true,
  });
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
