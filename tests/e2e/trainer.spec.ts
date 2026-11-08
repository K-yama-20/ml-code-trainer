import { test, expect, type Page } from "./qa-fixture";
import { mkdir } from "node:fs/promises";
import { historicalSession } from "./legacy-fixture";
async function editorCode(page: Page, code: string) {
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  await editor.press("ControlOrMeta+A");
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate((text) => navigator.clipboard.writeText(text), code);
  await editor.press("ControlOrMeta+V");
  await expect(page.locator(".view-lines")).toContainText(
    code
      .split("\n")
      .find((l) => l.trim().startsWith("return"))
      ?.trim() ?? "def solve",
  );
}
async function exercise(page: Page, concept = "NP05", problem = "NP05-01") {
  await page.goto("/home");
  await expect(
    page.getByRole("heading", { name: "今日も、コードを読む力を。" }),
  ).toBeVisible();
  if ((page.viewportSize()?.width ?? 0) >= 1024) {
    await mkdir("artifacts", { recursive: true });
    await page.screenshot({ path: "artifacts/home.png", fullPage: true });
  }
  const res = await page.request.post("/api/v1/sessions", {
    data: { kind: "custom", concept_id: concept, count: 6 },
  });
  expect(res.ok()).toBe(true);
  const session = await res.json();
  historicalSession(session.id);
  const item = session.items.find((i: { problem_version_id: string }) =>
    i.problem_version_id.startsWith(problem + "@"),
  );
  await page.goto(`/drill/s/${session.id}/${item.id}`);
  if ((page.viewportSize()?.width ?? 1440) < 1024)
    await page.getByRole("tab", { name: "回答・結果", exact: true }).click();
  await expect(
    page.getByRole("textbox", { name: "Editor content", exact: true }),
  ).toBeVisible({ timeout: 30000 });
  return { session, item };
}

test("NumPy run, submit, error, drafts and resume work end to end", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const { session, item } = await exercise(page);
  const code =
    'def solve(x):\n    print("row means")\n    return x.mean(axis=1)\n';
  await editorCode(page, code);
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toHaveText(/正解です/, {
    timeout: 150000,
  });
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    0,
  );
  await page
    .locator("details > summary")
    .filter({ hasText: "出力（print）" })
    .click();
  await expect(page.locator(".console-output")).toContainText("row means");
  await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
  await expect
    .poll(
      async () =>
        (await (await page.request.get("/api/v1/history")).json()).total,
      { timeout: 150000 },
    )
    .toBe(1);
  await page.screenshot({
    path: "artifacts/drill-accepted.png",
    fullPage: true,
  });
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    1,
  );
  await editorCode(page, "def solve(x):\n    return x.sum(axis=1)\n");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toHaveText(/結果が異なります/, {
    timeout: 150000,
  });
  await expect(page.locator(".view-lines")).toContainText("x.sum(axis=1)");
  await editorCode(page, "def solve(x):\n    return missing_name\n");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toHaveText(/実行中にエラー/, {
    timeout: 150000,
  });
  await expect(page.locator(".stderr")).toContainText("NameError");
  await editorCode(page, code);
  await expect
    .poll(
      async () =>
        (await (await page.request.get(`/api/v1/drafts/${item.id}`)).json())
          .code,
      { timeout: 15000 },
    )
    .toBe(code);
  await page.reload();
  await expect(page.locator(".view-lines")).toContainText("x.mean(axis=1)");
  await page.locator(".drill-top .drill-menu summary").click();
  await page.getByRole("button", { name: "中断して保存", exact: true }).click();
  await expect(page).toHaveURL("/home");
  await page.getByRole("button", { name: "学習を再開", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(session.id));
  expect(errors).toEqual([]);
});

test("wrong shape, syntax errors, timeout and stale results are visible", async ({
  page,
}) => {
  await exercise(page);
  await editorCode(page, "def solve(x):\n    return (\n");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toHaveText(/コードの書き方/, {
    timeout: 150000,
  });
  await editorCode(page, "def solve(x):\n    while True:\n        pass\n");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect(page.locator(".verdict")).toHaveText(/実行時間の上限/, {
    timeout: 150000,
  });
  await editorCode(page, "def solve(x):\n    return x.mean(axis=1)\n");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await editorCode(page, "def solve(x):\n    return 0\n");
  await expect(page.locator(".stale-notice")).toBeVisible({ timeout: 150000 });
});

test("PyTorch without Sandbox shows configuration error, no accepted result", async ({
  page,
}) => {
  await exercise(page, "PT04", "PT04-01");
  await expect(page.locator(".runtime-unavailable")).toContainText(
    "実行できません",
  );
  await expect(
    page.getByRole("button", { name: "実行のみ", exact: true }),
  ).toBeDisabled();
  await expect(page.locator(".verdict")).toHaveCount(0);
  expect((await (await page.request.get("/api/v1/history")).json()).total).toBe(
    0,
  );
});

test("Deep Dive and reading projects grade deterministic choices", async ({
  page,
}) => {
  await page.goto("/deep-dive/axis");
  await page.getByRole("radio", { name: "A (3,)", exact: true }).click();
  await page.getByRole("button", { name: "回答を確認", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("正解です");
  await page.goto("/reading/numpy-preprocessing");
  await expect(
    page.getByRole("heading", { name: "NumPyでつくる前処理パイプライン" }),
  ).toBeVisible();
  await page.getByRole("radio", { name: "A skiprows=1", exact: true }).click();
  await page.getByRole("button", { name: "回答を確認", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("正解です");
  await page
    .getByLabel("関数定義へジャンプ")
    .selectOption("features.py:fit_stats");
  await expect(page.locator(".reading-code .editor-heading")).toContainText(
    "features.py",
  );
});

test("mobile pages fit viewport and navigation remains usable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of [
    "/",
    "/home",
    "/curriculum",
    "/drill",
    "/reading",
    "/analytics",
    "/history",
    "/settings",
  ]) {
    await page.goto(path);
    await expect(page.locator("h1")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }
  await page
    .getByRole("button", { name: "メニューを開く", exact: true })
    .click();
  await page.getByRole("link", { name: "Drill 288", exact: true }).click();
  await expect(page).toHaveURL("/drill");
  await exercise(page);
  await page.getByRole("tab", { name: "回答・結果", exact: true }).click();
  await expect(
    page.getByRole("textbox", { name: "Editor content", exact: true }),
  ).toBeVisible();
});

test("settings persist and the light theme works", async ({ page }) => {
  await page.goto("/settings");
  await page.getByLabel("表示名", { exact: true }).fill("E2E Learner");
  await page.getByLabel("テーマ", { exact: true }).selectOption("light");
  await page.getByLabel("1日の目標問題数", { exact: true }).fill("30");
  await page.getByRole("button", { name: "変更を保存", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("設定を保存");
  await page.reload();
  await expect(page.getByLabel("表示名", { exact: true })).toHaveValue(
    "E2E Learner",
  );
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});
