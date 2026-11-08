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

test("empty answers explain the field; input replacement fails and a correct in-place alternative succeeds", async ({
  page,
}) => {
  await page.goto("/home");
  await expect(
    page.getByRole("button", { name: "学習を再開", exact: true }),
  ).toBeVisible();
  const s = await (
    await page.request.post("/api/v1/sessions", {
      data: { kind: "custom", concept_id: "NP05", count: 6 },
    })
  ).json();
  const item = s.items.find((i: { problem_version_id: string }) =>
    i.problem_version_id.startsWith("NP05-03@"),
  );
  await page.goto(`/drill/s/${s.id}/${item.id}`);
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(page.locator(".execution-notice")).toContainText(
    "解答欄にコードを入力",
  );
  await expect(page.locator(".verdict")).toHaveCount(0);
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  async function write(value: string) {
    await page
      .context()
      .grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.evaluate((s) => navigator.clipboard.writeText(s), value);
    await editor.press("ControlOrMeta+A");
    await editor.press("ControlOrMeta+V");
  }
  await write(
    "globals()['x'] = np.array([[1.,2.],[3.,4.],[5.,6.]])\nresult = x.sum(axis=0)\n",
  );
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toContainText("結果が異なります", {
    timeout: 150000,
  });
  await expect(page.locator(".case-result").first()).toContainText(
    "入力変数が再定義",
  );
  await write("x *= 2\nresult = x.sum(axis=0) / 2\n");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({ timeout: 150000 });
  await expect(page.locator(".submission-note")).toContainText("履歴に保存");
});

for (const p of all.filter(
  (p: { workspace: { authored: boolean } }) => p.workspace.authored,
))
  test(`authored ${p.id}: actual input and appropriate answer field`, async ({
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
    await expect(page.locator(".problem-description")).toHaveText(
      p.workspace.task,
    );
    await expect(page.getByText("公開テスト", { exact: true })).toHaveCount(0);
    await expect(page.getByText("よくある間違い", { exact: true })).toHaveCount(
      0,
    );
    if (p.type === "prediction")
      await expect(page.locator("#prediction-value")).toBeVisible();
    else {
      await expect(page.getByLabel("用意された入力コード")).toContainText(
        p.workspace.provided_code,
      );
      expect(
        await page
          .locator(
            ".provided-input input, .provided-input textarea, .provided-input [contenteditable=true]",
          )
          .count(),
      ).toBe(0);
      if (p.stage === "guided" && p.starter_code.split("___").length === 2)
        await expect(
          page.getByRole("textbox", { name: "コードの空欄" }),
        ).toBeVisible();
      else
        await expect(
          page.getByRole("textbox", { name: "Editor content", exact: true }),
        ).toBeVisible();
    }
    await page.screenshot({
      path: `docs/ux-concrete/after-${p.id}.png`,
      fullPage: true,
    });
  });

test("light theme, mobile and short desktop keep concrete inputs and answer action usable", async ({
  page,
}) => {
  await page.goto("/home");
  await expect(
    page.getByRole("button", { name: "学習を再開", exact: true }),
  ).toBeVisible();
  const s = await (
    await page.request.post("/api/v1/sessions", {
      data: { kind: "custom", concept_id: "NP05", count: 6 },
    })
  ).json();
  const item = s.items.find((i: { problem_version_id: string }) =>
    i.problem_version_id.startsWith("NP05-01@"),
  );
  for (const [width, height] of [
    [390, 844],
    [768, 1024],
    [1280, 640],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(`/drill/s/${s.id}/${item.id}`);
    if (width < 1024)
      await page.getByRole("button", { name: "回答欄へ", exact: true }).click();
    await expect(
      page.getByRole("textbox", { name: "コードの空欄" }),
    ).toBeVisible();
    await expect(page.getByLabel("用意された入力コード")).toBeVisible();
    const button = await page
      .getByRole("button", { name: "答え合わせ", exact: true })
      .boundingBox();
    expect(button!.y + button!.height).toBeLessThanOrEqual(height);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `docs/ux-concrete/after-${width}x${height}.png`,
      fullPage: true,
    });
  }
  await page.goto("/settings");
  await page.getByLabel("テーマ", { exact: true }).selectOption("light");
  await page.getByRole("button", { name: "変更を保存", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("設定を保存");
  await page.goto(`/drill/s/${s.id}/${item.id}`);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.screenshot({
    path: "docs/ux-concrete/after-light.png",
    fullPage: true,
  });
});
