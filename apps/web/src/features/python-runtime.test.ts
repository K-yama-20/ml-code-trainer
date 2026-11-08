import { afterEach, beforeEach, expect, it, vi } from "vitest";

let python: typeof import("./python-runtime");
let release: () => void;
const flush = () => vi.advanceTimersByTimeAsync(0);
const result = { outputs: [], stdout: "", stderr: "", static_ok: true };
const payload = { code: "result = 1", cases: [], packages: ["numpy"] };
const sandbox = Object.getOwnPropertyDescriptor(
  HTMLIFrameElement.prototype,
  "sandbox",
);

function frame() {
  const element = document.querySelector<HTMLIFrameElement>(
    'iframe[title="隔離されたPython実行環境"]',
  )!;
  const source = element.contentWindow!;
  const channel = JSON.parse(
    element.srcdoc.match(/const channel=("[^"]+");/)![1],
  );
  const send = vi.spyOn(source, "postMessage").mockImplementation(() => {});
  return {
    element,
    send,
    emit(data: Record<string, unknown>) {
      window.dispatchEvent(
        new MessageEvent("message", {
          source,
          data: { channel, ...data },
        }),
      );
    },
    request(command: string) {
      return send.mock.calls
        .map(([data]) => data)
        .find((data) => data.command === command)?.payload;
    },
  };
}
type Frame = ReturnType<typeof frame>;

async function initialize(worker: Frame) {
  worker.emit({ phase: "ready" });
  await flush();
  expect(worker.request("init")).toBeDefined();
  worker.emit({ phase: "initialized" });
  await flush();
}

async function prepared(worker: Frame) {
  expect(worker.request("prepare")?.packages).toEqual(["numpy"]);
  worker.emit({ phase: "prepared", id: worker.request("prepare").id });
  await flush();
}

async function retireFirstRun() {
  python.warmPython();
  const first = frame();
  await initialize(first);
  const run = python.runInPython(
    payload,
    vi.fn(),
    new AbortController().signal,
  );
  await flush();
  await prepared(first);
  first.emit({
    phase: "complete",
    id: first.request("run").id,
    result,
    retire: true,
  });
  // The result must resolve before the replacement has even initialized.
  await expect(run).resolves.toMatchObject({ result });
  await flush();
  expect(first.send.mock.calls.some(([data]) => data.command === "stop")).toBe(
    true,
  );
  return frame();
}

beforeEach(async () => {
  // jsdom does not implement the iframe's sandbox token list.
  if (!sandbox)
    Object.defineProperty(HTMLIFrameElement.prototype, "sandbox", {
      configurable: true,
      get: () => ({ add() {} }),
    });
  vi.resetModules();
  vi.useFakeTimers();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      text: async () => "# runtime harness",
    }),
  );
  python = await import("./python-runtime");
  release = python.keepPythonActive();
});

afterEach(async () => {
  release();
  await flush();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  if (!sandbox) Reflect.deleteProperty(HTMLIFrameElement.prototype, "sandbox");
});

it("shares a replacement and its package preparation with an immediate resubmission", async () => {
  const replacement = await retireFirstRun();
  const next = python.runInPython(
    payload,
    vi.fn(),
    new AbortController().signal,
  );
  expect(document.querySelectorAll("iframe")).toHaveLength(1);
  await initialize(replacement);
  expect(replacement.request("run")).toBeUndefined();
  await prepared(replacement);
  expect(
    replacement.send.mock.calls.filter(([data]) => data.command === "prepare"),
  ).toHaveLength(1);
  expect(
    replacement.send.mock.calls.filter(([data]) => data.command === "run"),
  ).toHaveLength(1);
  let settled = false;
  void next.then(() => {
    settled = true;
  });
  replacement.emit({ phase: "complete", id: "previous-run", result });
  await flush();
  expect(settled).toBe(false);
  replacement.emit({
    phase: "complete",
    id: replacement.request("run").id,
    result,
  });
  await next;
});

it("stops a failed preparation without retrying until an explicit run", async () => {
  const replacement = await retireFirstRun();
  await initialize(replacement);
  replacement.emit({
    phase: "error",
    id: replacement.request("prepare").id,
    message: "package failed",
  });
  await flush();
  await vi.advanceTimersByTimeAsync(120001);
  expect(document.querySelectorAll("iframe")).toHaveLength(0);
  const next = python.runInPython(
    payload,
    vi.fn(),
    new AbortController().signal,
  );
  const retry = frame();
  await initialize(retry);
  await prepared(retry);
  retry.emit({ phase: "complete", id: retry.request("run").id, result });
  await expect(next).resolves.toMatchObject({ result });
});

it("terminates preparation and a waiting resubmission when the Drill page leaves", async () => {
  const replacement = await retireFirstRun();
  await initialize(replacement);
  const next = python.runInPython(
    payload,
    vi.fn(),
    new AbortController().signal,
  );
  const rejected = expect(next).rejects.toThrow("停止");
  release();
  release = () => {};
  await rejected;
  await flush();
  replacement.emit({
    phase: "prepared",
    id: replacement.request("prepare").id,
  });
  await vi.advanceTimersByTimeAsync(120001);
  expect(replacement.request("run")).toBeUndefined();
  expect(document.querySelectorAll("iframe")).toHaveLength(0);
});
