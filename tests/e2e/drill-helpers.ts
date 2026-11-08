import { expect, type Page } from "./qa-fixture";

import { pinProblemVersion } from "./legacy-fixture";

export async function drillItem(page: Page, version: string) {
  const [id, revision] = version.split("@");
  const concept = id.split("-")[0];
  await page.goto("/home");
  await expect(
    page.getByRole("button", { name: "学習を再開", exact: true }),
  ).toBeVisible();
  const session = await (
    await page.request.post("/api/v1/sessions", {
      data: { kind: "custom", concept_id: concept, count: 50 },
    })
  ).json();
  const item = session.items.find((i: { problem_version_id: string }) =>
    i.problem_version_id.startsWith(id + "@"),
  );
  if (revision) pinProblemVersion(item.id, version);
  await page.goto(`/drill/s/${session.id}/${item.id}`);
  await expect(page.locator(".monaco-editor")).toHaveCount(1);
  return {
    editor: page.getByRole("textbox", { name: "Editor content", exact: true }),
    lines: page.locator(".view-lines"),
    session,
    item,
  };
}
