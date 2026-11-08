import { afterEach, expect, test, vi } from "vitest";
import { browserRun } from "./python";
import { runInPython } from "./python-runtime";
import type { Problem } from "../types/domain";

vi.mock("./python-runtime", () => ({
  runInPython: vi.fn(),
  timeoutResult: Symbol("timeout"),
}));
afterEach(() => vi.unstubAllGlobals());

test("the browser result keeps actual and expected type paths independently through JSON", async () => {
  vi.stubGlobal("performance", { now: () => 0, measure: vi.fn() });
  vi.mocked(runInPython).mockResolvedValue({
    channel: "test",
    phase: "complete",
    message: "",
    result: {
      outputs: [{ value: [[7]], tuple_paths: [[0]] }],
      stdout: "",
      stderr: "",
      static_ok: true,
    },
    elapsed_ms: 1,
  });
  const problem = {
    public_tests: [
      { setup: "", args: "", expected: [[9]], expected_tuple_paths: [[]] },
    ],
    packages: [],
    required_ast: "",
    check_dtype: false,
  } as unknown as Problem;
  const result = JSON.parse(
    JSON.stringify(
      await browserRun(
        problem,
        "result = [(7,)]",
        () => {},
        new AbortController().signal,
      ),
    ),
  );
  expect(result.verdict).toBe("Wrong Answer");
  expect(result.tests[0]).toMatchObject({
    actual: [[7]],
    actual_tuple_paths: [[0]],
    expected: [[9]],
    expected_tuple_paths: [[]],
  });
});
