import { test, expect } from "./qa-fixture";
import { drillItem } from "./drill-helpers";

test("warm Python is reused, stateful code is discarded, timeout recovers", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const phases: { phase: string; packages?: string[] }[] = [];
    Reflect.set(window, "__runtimePhases", phases);
    addEventListener("message", ({ data }) => {
      if (data?.channel && data.phase)
        phases.push({
          phase: data.phase,
          packages: data.timings?.packages_loaded,
        });
    });
  });
  const { editor, session } = await drillItem(page, "PY01-03@3");
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  const phases = () =>
    page.evaluate(
      () =>
        Reflect.get(window, "__runtimePhases") as {
          phase: string;
          packages?: string[];
        }[],
    );
  const count = async (phase: string) =>
    (await phases()).filter((p) => p.phase === phase).length;
  const run = async (code: string, result = "正解です") => {
    await page.evaluate((s) => navigator.clipboard.writeText(s), code);
    await editor.press("ControlOrMeta+A");
    await editor.press("ControlOrMeta+V");
    await page.getByRole("button", { name: "実行のみ", exact: true }).click();
    await expect(page.locator(".verdict strong")).toHaveText(result, {
      timeout: 150000,
    });
  };
  const answer = "result = dict(zip(keys, values))";
  await run("leak = 123\n" + answer);
  await run("print(leak)\n" + answer, "実行中にエラーがありました");
  await expect(page.locator(".stderr")).toContainText("leak");
  expect(await count("initialized")).toBe(1);
  await run("open('/tmp/trainer-leak', 'w').close()\n" + answer);
  await run(
    "open('/tmp/trainer-leak').close()\n" + answer,
    "実行中にエラーがありました",
  );
  await expect(page.locator(".stderr")).toContainText("No such file");
  // Each completed stateful run starts its replacement while the learner edits.
  await expect.poll(() => count("initialized")).toBe(3);
  await run("while True: pass", "実行時間の上限を超えました");
  await run(answer);
  expect(await count("initialized")).toBe(4);

  const visit = async (id: string) => {
    await page.evaluate((path) => {
      history.pushState(null, "", path);
      dispatchEvent(new PopStateEvent("popstate"));
    }, pathFor(id));
  };
  const pathFor = (id: string) => `/drill/s/${session.id}/${id}`;
  const numpy = await (
    await page.request.post("/api/v1/sessions", {
      data: { kind: "custom", concept_id: "NP05", count: 6 },
    })
  ).json();
  const item = numpy.items.find((i: { problem_version_id: string }) =>
    i.problem_version_id.startsWith("NP05-01@"),
  );
  // NP05-01 provides `x = np.array(...)`; the learner writes only the result line.
  const numpyAnswer = "result = np.mean(x, axis=1)";
  await page.evaluate((path) => {
    history.pushState(null, "", path);
    dispatchEvent(new PopStateEvent("popstate"));
  }, `/drill/s/${numpy.id}/${item.id}`);
  await expect(page.locator(".view-lines")).toContainText("np.array");
  await run(numpyAnswer);
  await run(numpyAnswer);
  expect(await count("initialized")).toBe(4);
  expect((await phases()).flatMap((p) => p.packages ?? [])).toEqual(["numpy"]);
  await visit(
    session.items.find((i: { problem_version_id: string }) =>
      i.problem_version_id.startsWith("PY01-03@"),
    ).id,
  );
  await expect(page.locator(".problem-content h1")).toHaveText(
    "zipで辞書を作る",
  );
  await expect(page.locator(".verdict")).toHaveCount(0);
  await run(answer);
  expect(await count("initialized")).toBe(4);

  const oldFrame = await page
    .locator('iframe[title="隔離されたPython実行環境"]')
    .elementHandle();
  const previousRuns = await count("running");
  await page.evaluate(() => navigator.clipboard.writeText("while True: pass"));
  await editor.press("ControlOrMeta+A");
  await editor.press("ControlOrMeta+V");
  await page.getByRole("button", { name: "実行のみ", exact: true }).click();
  await expect.poll(() => count("running")).toBe(previousRuns + 1);
  await page.evaluate((path) => {
    history.pushState(null, "", path);
    dispatchEvent(new PopStateEvent("popstate"));
  }, `/drill/s/${numpy.id}/${item.id}`);
  await expect(page.locator(".view-lines")).toContainText("np.array");
  await expect
    .poll(() => oldFrame!.evaluate((frame) => frame.isConnected))
    .toBe(false);
  await run(numpyAnswer);
  expect(await count("initialized")).toBe(5);
});
