import { test, expect } from "./qa-fixture";
import { drillItem } from "./drill-helpers";

test("the Workspace drawer isolates Drill and saves a draft before navigation", async ({
  page,
}) => {
  const { editor, item, lines } = await drillItem(page, "PY01-01");
  const drillUrl = page.url();
  const trigger = page.getByRole("button", { name: "メニューを開く" });
  const drawer = page.getByRole("dialog", { name: "Workspaceナビゲーション" });
  const close = drawer.getByRole("button", { name: "メニューを閉じる" });
  const settings = drawer.getByRole("link", { name: "設定" });
  const hint = page.locator(".drill-hints");
  const solution = page.locator(".solution-accordion");
  const editorNode = await page.locator(".monaco-editor").elementHandle();
  const editorInput = await editor.elementHandle();
  const bounds = () =>
    Promise.all(
      [".drill-workspace", ".problem-pane", ".monaco-editor"].map((selector) =>
        page.locator(selector).boundingBox(),
      ),
    );
  await expect(editor).toBeFocused();
  await page.keyboard.insertText("[n * 2 for n in numbers]");
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("Alt+h");
  await expect(hint).toHaveAttribute("open", "");
  const original = await bounds();

  await trigger.click();
  await expect(drawer).toBeVisible();
  await expect(close).toBeFocused();
  await expect(drawer.getByRole("link", { name: /^Drill/ })).toHaveAttribute(
    "aria-current",
    "page",
  );
  expect(await bounds()).toEqual(original);
  expect(
    await drawer.evaluate(
      (element) => getComputedStyle(element, "::backdrop").backgroundColor,
    ),
  ).toBe("rgba(0, 0, 0, 0.48)");
  await page.keyboard.press("Shift+Tab");
  await expect(settings).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();
  await editorInput?.evaluate((element) => (element as HTMLElement).focus());
  await expect(close).toBeFocused();
  await page.keyboard.type("abc");
  for (const key of [
    "Alt+h",
    "Alt+j",
    "Control+Enter",
    "Control+Shift+Enter",
  ]) {
    await page.keyboard.press(key);
  }
  await expect(hint).toHaveAttribute("open", "");
  await expect(solution).not.toHaveAttribute("open", "");
  await expect(page.locator(".verdict")).toHaveCount(0);
  await expect(page).toHaveURL(drillUrl);
  await expect(lines).toContainText("result = [n * 2 for n in numbers]");

  await page.keyboard.press("Escape");
  await expect(drawer).not.toBeVisible();
  await expect(trigger).toBeFocused();
  expect(await bounds()).toEqual(original);
  expect(await editorNode?.evaluate((element) => element.isConnected)).toBe(
    true,
  );
  await editor.focus();
  await page.keyboard.insertText(" ");
  await expect(lines).toContainText("result = [n * 2 for n in numbers ]");

  await trigger.click();
  await close.click();
  await expect(drawer).not.toBeVisible();
  await trigger.click();
  // The visible editor is under the backdrop. Its click dismisses the drawer.
  await page.mouse.click(900, 300);
  await expect(drawer).not.toBeVisible();
  await expect(trigger).toBeFocused();

  await page.getByRole("button", { name: "テーマを切り替える" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.setViewportSize({ width: 360, height: 520 });
  const mobileBounds = await bounds();
  const beforeScroll = await page.evaluate(() => window.scrollY);
  await trigger.click();
  expect(await bounds()).toEqual(mobileBounds);
  expect(
    await drawer.evaluate(
      (element) => getComputedStyle(element, "::backdrop").backgroundColor,
    ),
  ).toBe("rgba(0, 0, 0, 0.33)");
  await page.mouse.move(355, 350);
  await page.mouse.wheel(0, 400);
  await page.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
  expect(await page.evaluate(() => window.scrollY)).toBe(beforeScroll);
  await settings.click();
  await expect(page).toHaveURL(/\/settings$/);
  const saved = await (
    await page.request.get(`/api/v1/drafts/${item.id}`)
  ).json();
  expect(saved.code).toBe("result = [n * 2 for n in numbers ]");
  await page.goBack();
  await expect(page).toHaveURL(drillUrl);
  await page.getByRole("tab", { name: "回答・結果" }).click();
  await expect(lines).toContainText("result = [n * 2 for n in numbers ]");
});
