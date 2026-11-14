import { test, expect } from "./qa-fixture";
import { drillItem } from "./drill-helpers";

test("blank remains empty and fixed boundaries use native editor history", async ({
  page,
}) => {
  const { editor, lines, item } = await drillItem(page, "PY02-01@3");
  await expect(lines).toContainText("result = scale_values(x)");
  await expect(lines).not.toContainText("___");
  await expect(page.locator(".drill-blank")).toHaveCount(0);
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await editor.press("ControlOrMeta+A");
  await editor.press("Backspace");
  await editor.press("Delete");
  await editor.press("x");
  await expect(lines).toContainText("return x");
  await editor.press("Backspace");
  await expect(lines).not.toContainText("return x");
  await editor.press("Backspace");
  await editor.press("Delete");
  await editor.press("y");
  await expect(lines).toContainText("return y");
  await editor.press("ArrowLeft");
  await editor.press("Delete");
  await expect(lines).not.toContainText("return y");
  await editor.press("ControlOrMeta+z");
  await expect(lines).toContainText("return y");
  await editor.press("ControlOrMeta+y");
  await expect(lines).not.toContainText("return y");
  await expect(lines).not.toContainText("___");

  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Input.imeSetComposition", {
    text: "にほん",
    selectionStart: 3,
    selectionEnd: 3,
  });
  await cdp.send("Input.insertText", { text: "日本" });
  await expect(lines).toContainText("return 日本");
  await editor.press("ControlOrMeta+A");
  await editor.press("ControlOrMeta+c");
  await expect
    .poll(() => page.evaluate(() => navigator.clipboard.readText()))
    .toBe("日本");

  await page.evaluate(() =>
    navigator.clipboard.writeText("[\n        v * scale for v in x\n    ]"),
  );
  await editor.press("ControlOrMeta+v");
  await expect(lines).toContainText("v * scale for v in x");
  await editor.press("ControlOrMeta+Home");
  await editor.press("ControlOrMeta+Shift+End");
  await editor.press("Delete");
  await expect(lines).toContainText("result = scale_values(x)");
  await expect(lines).toContainText("v * scale for v in x");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({ timeout: 150000 });
  await page.reload();
  await expect(lines).toContainText("v * scale for v in x");
  await page.getByRole("button", { name: "次の問題", exact: true }).click();
  await expect(page).not.toHaveURL(new RegExp(item.id + "$"));
  await expect(page.locator(".problem-content h1")).toBeVisible();
});

test("model answer exposes copyable Python operators", async ({ page }) => {
  await drillItem(page, "PY01-05@2");
  await page.locator(".solution-accordion summary").click();
  const solution = page.locator(".solution-accordion pre");
  await expect(solution).toBeVisible();
  expect(
    await solution.evaluate(
      (node) => getComputedStyle(node).fontVariantLigatures,
    ),
  ).toBe("none");
  await expect(solution).toContainText("!=");
  await expect(solution).not.toContainText("≠");
});

test("a multi-step split answer runs after the fixed import and input", async ({
  page,
}) => {
  const { editor, lines } = await drillItem(page, "SK01-01");
  await expect(lines).toContainText(
    "from sklearn.model_selection import train_test_split",
  );
  await expect(lines).not.toContainText("___");
  await page.locator(".solution-accordion summary").click();
  await expect(page.locator(".solution-accordion pre")).toContainText(
    "result = (len(X_train), len(X_test))",
  );
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate(() =>
    navigator.clipboard.writeText(
      "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)\n" +
        "result = (len(X_train), len(X_test))",
    ),
  );
  await editor.press("ControlOrMeta+A");
  await editor.press("ControlOrMeta+V");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "次の問題", exact: true }),
  ).toBeVisible({
    timeout: 150000,
  });
});
