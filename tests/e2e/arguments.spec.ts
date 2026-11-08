import { test, expect } from "./qa-fixture";

test("PY02 submits calls, function definitions and multiline return expressions", async ({
  page,
}) => {
  await page.goto("/concepts/PY02");
  await page.getByRole("button", { name: "演習を開始", exact: true }).click();
  await expect(page.locator(".problem-content h1")).toHaveText(
    "位置引数を使って関数を呼び出す",
  );
  const sessionId = new URL(page.url()).pathname.split("/")[3];
  const session = await (
    await page.request.get(`/api/v1/sessions/${sessionId}`)
  ).json();
  expect(session.items).toHaveLength(18);
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);

  const examples = [
    {
      index: 1,
      title: "キーワード引数を使って関数を呼び出す",
      fixed: "def clip(x, lower, upper):",
      answer: "clip(upper=upper, x=x, lower=lower)",
      completed: "result = clip(upper=upper, x=x, lower=lower)",
    },
    {
      index: 7,
      title: "任意個のLossの平均を求める",
      fixed: "result = average_loss(0.2, 0.4, 0.6)",
      answer:
        "def average_loss(*losses):\n    return sum(losses) / len(losses)",
      completed: "return sum(losses) / len(losses)",
    },
    {
      index: 11,
      title: "必要な学習パラメータだけを抽出する",
      fixed: "result = pick_training_params(",
      answer:
        '{\n        k: v\n        for k, v in params.items()\n        if k in ("lr", "batch_size")\n    }',
      completed: "return {",
    },
    {
      index: 17,
      title: "*argsと**kwargsを別の関数へ渡す",
      fixed: "def compute_error(pred, target, absolute=False):",
      answer: "fn(*args, **kwargs)",
      completed: "return fn(*args, **kwargs)",
    },
  ];
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  const lines = page.locator(".view-lines");
  for (const { index, title, fixed, answer, completed } of examples) {
    const item = session.items[index];
    await page.goto(`/drill/s/${sessionId}/${item.id}`);
    await expect(page.locator(".problem-content h1")).toHaveText(title);
    await expect(page.locator(".monaco-editor")).toHaveCount(1);
    await expect(lines).toContainText(fixed);
    await expect(lines).not.toContainText("___");
    await page.evaluate((text) => navigator.clipboard.writeText(text), answer);
    await editor.press("ControlOrMeta+A");
    await editor.press("ControlOrMeta+V");
    await expect(lines).toContainText(completed);
    if (index === 11) {
      await editor.press("ControlOrMeta+Home");
      await editor.press("ControlOrMeta+Shift+End");
      await editor.press("Delete");
      await expect(lines).toContainText(fixed);
      await expect(lines).toContainText(completed);
      await page.locator(".solution-accordion summary").click();
      await expect(page.locator(".solution-accordion pre")).toContainText(
        "def pick_training_params(**params):",
      );
      await expect(lines).toContainText(completed);
    }
    await editor.press("ControlOrMeta+Enter");
    await expect(
      page.getByRole("button", { name: "次の問題", exact: true }),
    ).toBeVisible({ timeout: 150000 });
  }
});
