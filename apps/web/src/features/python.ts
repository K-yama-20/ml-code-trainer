import { runInPython, timeoutResult } from "./python-runtime";
import type { Problem, Result } from "../types/domain";
export function equivalent(
  a: unknown,
  b: unknown,
  checkDtype = false,
  comparison: "exact" | "json" | "json_unicode" | "relative" = "exact",
): boolean {
  if (comparison === "relative") return relativeEquivalent(a, b, checkDtype);
  if (comparison !== "exact") {
    if (typeof a !== "string" || typeof b !== "string") return false;
    if (
      comparison === "json_unicode" &&
      [...b].some((char) => char.codePointAt(0)! > 127 && !a.includes(char))
    )
      return false;
    try {
      return equivalent(JSON.parse(a), JSON.parse(b), checkDtype);
    } catch {
      return false;
    }
  }
  if (typeof b === "number")
    return (
      typeof a === "number" && Math.abs(a - b) <= 1e-5 + 1e-5 * Math.abs(b)
    );
  if (Array.isArray(b))
    return (
      Array.isArray(a) &&
      a.length === b.length &&
      b.every((v, i) => equivalent(a[i], v, checkDtype))
    );
  if (b && typeof b === "object")
    return (
      !!a &&
      typeof a === "object" &&
      Object.keys(a).filter((k) => checkDtype || k !== "dtype").length ===
        Object.keys(b).filter((k) => checkDtype || k !== "dtype").length &&
      Object.entries(b).every(
        ([k, v]) =>
          (k === "dtype" && !checkDtype) ||
          equivalent((a as Record<string, unknown>)[k], v, checkDtype),
      )
    );
  return a === b;
}
// Values near 1e-16 (log1p/expm1) must not pass as 0 under an absolute floor.
function relativeEquivalent(
  a: unknown,
  b: unknown,
  checkDtype: boolean,
): boolean {
  if (typeof b === "number")
    return typeof a === "number" && Math.abs(a - b) <= 1e-5 * Math.abs(b);
  if (Array.isArray(b))
    return (
      Array.isArray(a) &&
      a.length === b.length &&
      b.every((v, i) => relativeEquivalent(a[i], v, checkDtype))
    );
  if (b && typeof b === "object")
    return (
      !!a &&
      typeof a === "object" &&
      Object.keys(a).filter((k) => checkDtype || k !== "dtype").length ===
        Object.keys(b).filter((k) => checkDtype || k !== "dtype").length &&
      Object.entries(b).every(
        ([k, v]) =>
          (k === "dtype" && !checkDtype) ||
          relativeEquivalent((a as Record<string, unknown>)[k], v, checkDtype),
      )
    );
  return a === b;
}
export async function browserRun(
  problem: Problem,
  code: string,
  onStatus: (s: string) => void,
  signal: AbortSignal,
): Promise<Result> {
  const data = await runInPython(
    {
      code,
      cases: problem.public_tests,
      packages: problem.packages,
      required: problem.required_ast,
      execution: problem.execution,
    },
    onStatus,
    signal,
  );
  if (data === timeoutResult)
    return {
      verdict: "Time Limit Exceeded",
      passed_tests: 0,
      total_tests: problem.public_tests.length,
      stderr: "5秒の実行上限を超えました。Workerを終了しました。",
    };
  const judgeStarted = performance.now();
  if (JSON.stringify(data).length > 100000)
    throw new Error("出力サイズの上限を超えました。");
  const result = data.result;
  const tests = problem.public_tests.map((test, i) => ({
    name: `Test ${i + 1}`,
    passed:
      !result.outputs[i]?.error &&
      !result.outputs[i]?.replaced_inputs &&
      !result.outputs[i]?.wrong_type &&
      !(problem.protect_inputs && result.outputs[i]?.mutated_inputs) &&
      equivalent(
        result.outputs[i]?.value,
        test.expected,
        problem.check_dtype,
        test.comparison,
      ),
    error: result.outputs[i]?.replaced_inputs
      ? "用意された入力変数が再定義されています。提供された入力を使って計算してください。"
      : problem.protect_inputs && result.outputs[i]?.mutated_inputs
        ? "入力データが変更されています。入力はそのまま使い、結果をresultに代入してください。"
        : result.outputs[i]?.wrong_type
          ? "resultの型を問題文に合わせてください。"
          : result.outputs[i]?.error,
    actual: result.outputs[i]?.value,
    expected: test.expected,
    actual_tuple_paths: result.outputs[i]?.tuple_paths,
    expected_tuple_paths: test.expected_tuple_paths,
  }));
  const passed = tests.filter((t) => t.passed).length;
  const error = result.outputs.find((o) => o.error);
  const verdict: Result = {
    verdict: error
      ? error.kind === "SyntaxError"
        ? "Syntax Error"
        : "Runtime Error"
      : passed === tests.length && result.static_ok
        ? "Accepted"
        : "Wrong Answer",
    passed_tests: passed,
    total_tests: tests.length,
    tests,
    stdout: result.stdout,
    stderr: error
      ? `${error.kind}: ${error.error}`
      : !result.static_ok
        ? "指定されたAPI・構文を使用してください。"
        : result.stderr,
    error_line: error?.line,
    elapsed_ms: data.elapsed_ms,
  };
  performance.measure("trainer:python-judge", { start: judgeStarted });
  return verdict;
}
