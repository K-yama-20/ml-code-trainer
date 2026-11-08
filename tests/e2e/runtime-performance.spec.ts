import { test, expect, type Page } from "./qa-fixture";
import { drillItem } from "./drill-helpers";

async function measure(page: Page, id: string, answer: string) {
  const { editor } = await drillItem(page, id);
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await expect(editor).toBeAttached();
  await page.evaluate((text) => navigator.clipboard.writeText(text), answer);
  await editor.press("ControlOrMeta+A");
  await editor.press("ControlOrMeta+V");
  const rows = [];
  const run = page.getByRole("button", { name: "実行のみ", exact: true });
  await page.evaluate(() => {
    const run =
      document.querySelector<HTMLButtonElement>(
        'button[aria-label="実行のみ"]',
      ) ??
      Array.from(document.querySelectorAll("button")).find(
        (button) => button.textContent?.trim() === "実行のみ",
      )!;
    const start = () =>
      Reflect.set(window, "__runtimeClicked", performance.now());
    run.addEventListener("click", start, true);
    document.addEventListener(
      "click",
      (e) => {
        if (
          e.target instanceof Element &&
          e.target.closest("button")?.textContent?.trim() === "実行のみ"
        )
          start();
      },
      true,
    );
  });
  for (let i = 0; i < 6; i++) {
    await run.click();
    await expect(page.getByText("正解です", { exact: true })).toBeVisible({
      timeout: 150000,
    });
    await expect(run).toBeEnabled();
    rows.push(
      await page.evaluate(() => {
        const at = Number(Reflect.get(window, "__runtimeClicked"));
        const samples = Reflect.get(window, "__runtimeSamples") as {
          at: number;
          phase: string;
        }[];
        return {
          total: performance.now() - at,
          phases: samples
            .filter((r) => r.at >= at)
            .map((r) => ({ ...r, at: r.at - at })),
          prewarm: samples.filter((r) => r.at < at && r.phase === "initialized")
            .length,
          judge: performance.getEntriesByName("trainer:python-judge").at(-1)
            ?.duration,
          api: performance
            .getEntriesByType("resource")
            .filter((r) => r.name.includes("/api/") && r.startTime >= at)
            .map((r) => ({ name: new URL(r.name).pathname, ms: r.duration })),
        };
      }),
    );
  }
  return rows;
}

for (const cold of [true, false]) {
  test(`runtime timings with ${cold ? "previous worker lifecycle" : "reuse"}`, async ({
    page,
  }) => {
    await page.addInitScript((bootPerRun) => {
      const rows: unknown[] = [];
      Reflect.set(window, "__runtimeSamples", rows);
      addEventListener("message", (event) => {
        const d = event.data;
        if (d?.channel && typeof d.phase === "string") {
          // Replay the previous lifetime policy without routing requests,
          // which would disable HTTP caching in Chromium.
          if (bootPerRun && d.phase === "complete") d.retire = true;
          rows.push({
            phase: d.phase,
            at: performance.now(),
            elapsed: d.elapsed_ms,
            timings: d.timings,
          });
        }
      });
    }, cold);
    for (const [id, answer] of [
      ["PY01-03@3", "result = dict(zip(keys, values))"],
      ["NP05-01", "1"],
    ]) {
      const data = await measure(page, id, answer);
      const warm = data.slice(1);
      expect(
        warm.every(
          (r) => r.phases.some((p) => p.phase === "initialized") === cold,
        ),
      ).toBe(true);
      console.log("RUNTIME_MEASUREMENTS " + JSON.stringify({ cold, id, data }));
    }
  });
}
