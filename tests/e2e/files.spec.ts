import { readFileSync } from "node:fs";
import { test, expect } from "./qa-fixture";

const lessons = JSON.parse(readFileSync("content/files.json", "utf8")) as {
  id: string;
  title: string;
  solution: string;
}[];

test("PY03 displays and submits path, JSON, read and append exercises", async ({
  page,
}) => {
  await page.goto("/concepts/PY03");
  await page.getByRole("button", { name: "演習を開始", exact: true }).click();
  await expect(page.locator(".problem-content h1")).toHaveText(
    lessons[0].title,
  );
  const sessionId = new URL(page.url()).pathname.split("/")[3];
  const session = await (
    await page.request.get(`/api/v1/sessions/${sessionId}`)
  ).json();
  expect(
    session.items.map(
      (item: { problem_version_id: string }) =>
        item.problem_version_id.split("@")[0],
    ),
  ).toEqual(lessons.map((lesson) => lesson.id));
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  const editor = page.getByRole("textbox", {
    name: "Editor content",
    exact: true,
  });
  const lines = page.locator(".view-lines");
  for (const index of [0, 7, 13, 16]) {
    const lesson = lessons[index];
    const item = session.items[index];
    await page.goto(`/drill/s/${sessionId}/${item.id}`);
    await expect(page.locator(".problem-content h1")).toHaveText(lesson.title);
    await expect(page.locator(".monaco-editor")).toHaveCount(1);
    await expect(lines).not.toContainText("___");
    if (index === 7)
      await expect(lines).toContainText('"channels": [16, 32, 64]');
    const answer =
      index === 16
        ? lesson.solution
        : lesson.solution.slice("result = ".length);
    await page.evaluate((text) => navigator.clipboard.writeText(text), answer);
    await editor.press("ControlOrMeta+A");
    await editor.press("ControlOrMeta+V");
    if (index === 16) {
      await expect(lines).toContainText(
        'result = path.read_text(encoding="utf-8")',
      );
      await editor.press("ControlOrMeta+Home");
      await editor.press("ControlOrMeta+Shift+End");
      await editor.press("Delete");
      await expect(lines).toContainText("f.write(new_line)");
      await page.getByRole("button", { name: "実行のみ", exact: true }).click();
      await expect(page.locator(".verdict")).toContainText("正解です", {
        timeout: 150000,
      });
      await page.getByRole("button", { name: "実行のみ", exact: true }).click();
      await expect(page.locator(".verdict")).toContainText("正解です", {
        timeout: 150000,
      });
    }
    await page.locator(".solution-accordion summary").click();
    await expect(page.locator(".solution-accordion pre")).toHaveText(
      lesson.solution,
    );
    await expect(lines).toContainText(
      index === 16 ? "f.write(new_line)" : lesson.solution,
    );
    await page.getByRole("button", { name: "答え合わせ", exact: true }).click();
    await expect(
      page.getByRole("button", { name: "次の問題", exact: true }),
    ).toBeVisible({
      timeout: 150000,
    });
  }
});
