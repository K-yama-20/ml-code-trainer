import { test, expect } from "./qa-fixture";
import { drillItem } from "./drill-helpers";

test("Drill shortcuts use the existing operations without interrupting editing", async ({
  page,
}) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, "platform", { value: "Win32" }),
  );
  const { editor, lines, item } = await drillItem(page, "PY01-01");
  const hint = page.locator(".drill-hints");
  const solution = page.locator(".solution-accordion");
  const submit = page.getByRole("button", { name: "答え合わせ", exact: true });
  const next = page.getByRole("button", { name: "次の問題", exact: true });
  await expect(editor).toBeFocused();
  await expect(hint.locator("kbd")).toHaveText("Alt + H");
  await expect(solution.locator("kbd")).toHaveText("Alt + J");
  await expect(submit.locator("kbd")).toHaveText("Ctrl + Enter");
  await page.keyboard.press("Control+Enter");
  await page.keyboard.press("Control+Shift+Enter");
  await expect(page.locator(".execution-notice")).toHaveCount(0);

  await page.keyboard.insertText("[n * 2 for n in numbers]");
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("Alt+h");
  await expect(hint).toHaveAttribute("open", "");
  await expect(hint.locator("p")).toContainText("リスト内包表記");
  await page.keyboard.press("Alt+h");
  await expect(hint).not.toHaveAttribute("open", "");
  await page.keyboard.press("Alt+j");
  await expect(solution.locator("pre")).toHaveText(
    "result = [n * 2 for n in numbers]",
  );
  await page.keyboard.press("Alt+j");
  await expect(solution).not.toHaveAttribute("open", "");
  await expect(editor).toBeFocused();
  await page.keyboard.insertText(" ");
  await expect(lines).toContainText("result = [n * 2 for n in numbers ]");
  await page.keyboard.press("Backspace");
  await expect(lines).toContainText("result = [n * 2 for n in numbers]");

  await hint.locator("summary").click();
  await expect(hint).toHaveAttribute("open", "");
  await hint.locator("summary").click();
  await expect(hint).not.toHaveAttribute("open", "");
  await solution.locator("summary").click();
  await expect(solution).toHaveAttribute("open", "");
  await solution.locator("summary").click();
  await expect(solution).not.toHaveAttribute("open", "");
  await editor.focus();

  await editor.evaluate((node) => {
    node.dispatchEvent(
      new CompositionEvent("compositionstart", { bubbles: true }),
    );
    node.dispatchEvent(
      new KeyboardEvent("keydown", {
        bubbles: true,
        altKey: true,
        key: "h",
        code: "KeyH",
      }),
    );
    node.dispatchEvent(
      new KeyboardEvent("keydown", {
        bubbles: true,
        ctrlKey: true,
        key: "Enter",
        isComposing: true,
      }),
    );
    node.dispatchEvent(
      new CompositionEvent("compositionend", { bubbles: true }),
    );
    node.dispatchEvent(
      new KeyboardEvent("keydown", {
        bubbles: true,
        altKey: true,
        key: "h",
        code: "KeyH",
        repeat: true,
      }),
    );
  });
  await expect(hint).not.toHaveAttribute("open", "");
  await expect(submit).toBeVisible();

  await page.keyboard.press("Control+Alt+Enter");
  await expect(page.locator(".verdict")).toContainText("正解です");
  await expect(next).toHaveCount(0);

  let requests = 0;
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/submissions", async (route) => {
    requests++;
    await gate;
    await route.continue();
  });
  try {
    await page.keyboard.press("Control+Enter");
    await expect.poll(() => requests, { timeout: 60000 }).toBe(1);
    await page.keyboard.press("Control+Enter");
    await page.keyboard.press("Control+Shift+Enter");
    await expect(page).toHaveURL(new RegExp(item.id + "$"));
  } finally {
    release();
  }
  await expect(next).toBeVisible();
  await expect(next.locator("kbd")).toHaveText("Ctrl + Shift + Enter");
  expect(requests).toBe(1);
  const saved = await (
    await page.request.get(`/api/v1/session-items/${item.id}/last-submission`)
  ).json();
  expect(saved).toMatchObject({
    submitted_code: "result = [n * 2 for n in numbers]",
    hint_level_used: 1,
    solution_viewed: true,
  });
  await page.keyboard.press("Control+Shift+Enter");
  await expect(page.locator(".problem-content h1")).toHaveText(
    "画素値を正規化する",
  );
  await expect(editor).toBeFocused();
  await page.keyboard.insertText("[p / 255 for p in pixels]");
  await expect(lines).toContainText("result = [p / 255 for p in pixels]");
  await submit.click();
  await expect(next).toBeVisible();
  await next.click();
  await expect(page.locator(".problem-content h1")).toHaveText(
    "各要素を二乗する",
  );
});

test("Mac labels match Option symbols and Meta shortcuts", async ({ page }) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, "platform", { value: "MacIntel" }),
  );
  const { editor } = await drillItem(page, "PY01-01");
  await expect(editor).toBeFocused();
  await expect(page.locator(".drill-hints kbd")).toHaveText("Option + H");
  await expect(page.locator(".solution-accordion kbd")).toHaveText(
    "Option + J",
  );
  await expect(
    page
      .getByRole("button", { name: "答え合わせ", exact: true })
      .locator("kbd"),
  ).toHaveText("Cmd + Enter");
  await page.keyboard.insertText("[2 * n for n in numbers]");
  await editor.dispatchEvent("keydown", {
    key: "˙",
    code: "KeyH",
    altKey: true,
  });
  await expect(page.locator(".drill-hints")).toHaveAttribute("open", "");
  await editor.dispatchEvent("keydown", {
    key: "∆",
    code: "KeyJ",
    altKey: true,
  });
  await expect(page.locator(".solution-accordion")).toHaveAttribute("open", "");
  await page.keyboard.press("Meta+Enter");
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }).locator("kbd"),
  ).toHaveText("Cmd + Shift + Enter");
  await page.keyboard.press("Meta+Shift+Enter");
  await expect(page.locator(".problem-content h1")).toHaveText(
    "画素値を正規化する",
  );
  await expect(editor).toBeFocused();
  await page.setViewportSize({ width: 800, height: 900 });
  await page.keyboard.press("Alt+h");
  await expect(page.locator(".drill-hints")).toBeVisible();
  await expect(page.locator(".drill-hints")).toHaveAttribute("open", "");
  await page.keyboard.press("Alt+h");
  await expect(editor).toBeFocused();
});
