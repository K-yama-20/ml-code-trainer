import { test, expect } from "./qa-fixture";

test("PY01 uses the authored order, one hint and protected expression input", async ({
  page,
}) => {
  await page.goto("/concepts/PY01");
  await expect(
    page.getByRole("heading", { name: "内包表記とイテレーション" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "演習を開始", exact: true }).click();
  await expect(page.locator(".problem-content h1")).toHaveText(
    "リストの各要素を2倍にする",
  );
  const [, , , sessionId] = new URL(page.url()).pathname.split("/");
  const session = await (
    await page.request.get(`/api/v1/sessions/${sessionId}`)
  ).json();
  expect(
    session.items.map((item: { problem_version_id: string }) =>
      Number(item.problem_version_id.split("-")[1].split("@")[0]),
    ),
  ).toEqual([1, 7, 8, 2, 9, 10, 3, 11, 12, 4, 13, 14, 5, 15, 16, 6, 17, 18]);
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  const lines = page.locator(".view-lines");
  await expect(lines).toContainText("numbers = [2, -1, 4]");
  await expect(lines).toContainText("# 以下に答えを記入");
  await expect(lines).toContainText("result =");
  await expect(lines).not.toContainText("___");
  await editor.press("ControlOrMeta+Home");
  await editor.press("ControlOrMeta+Shift+End");
  await editor.press("Backspace");
  await expect(lines).toContainText("numbers = [2, -1, 4]");
  await page.locator(".drill-hints summary").click();
  await expect(page.locator(".drill-hints p")).toHaveText(
    "リスト内包表記は [式 for 変数 in リスト] で記述します。",
  );
  await page.locator(".solution-accordion summary").click();
  await expect(page.locator(".solution-accordion pre")).toHaveText(
    "result = [n * 2 for n in numbers]",
  );

  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  const fill = async (expr: string) => {
    await page.evaluate((text) => navigator.clipboard.writeText(text), expr);
    await editor.press("ControlOrMeta+A");
    await editor.press("ControlOrMeta+V");
  };
  const run = () =>
    page.getByRole("button", { name: "実行のみ", exact: true }).click();
  const accepted = () =>
    expect(
      page.getByRole("button", { name: "次の問題", exact: true }),
    ).toBeVisible({ timeout: 150000 });
  await fill("list(map(lambda x: x * 2, numbers))");
  await run();
  await expect(page.locator(".verdict")).toContainText("結果が異なります", {
    timeout: 150000,
  });
  await fill("[value + value for value in numbers]");
  await page
    .getByRole("button", { name: /^(もう一度)?答え合わせ$/ })
    .click();
  await accepted();
  const draft = await (
    await page.request.get(`/api/v1/drafts/${session.items[0].id}`)
  ).json();
  expect(draft.code).toBe("result = [value + value for value in numbers]");
  await page.reload();
  await expect(lines).toContainText(
    "result = [value + value for value in numbers]",
  );
  await page.getByRole("button", { name: "次の問題", exact: true }).click();
  await expect(page.locator(".problem-content h1")).toHaveText(
    "画素値を正規化する",
  );
  await fill("[p / 255 for p in pixels]");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await accepted();

  await page.goto(`/drill/s/${sessionId}/${session.items[17].id}`);
  await expect(lines).toContainText("learning_rates = [0.1, 0.01]");
  await fill(
    "[[rate, size] for rate in learning_rates for size in batch_sizes]",
  );
  await run();
  await expect(page.locator(".verdict")).toContainText("結果が異なります", {
    timeout: 150000,
  });
  await fill(
    "[(rate, size) for rate in learning_rates for size in batch_sizes]",
  );
  await page
    .getByRole("button", { name: /^(もう一度)?答え合わせ$/ })
    .click();
  await accepted();
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    3,
  );
});

