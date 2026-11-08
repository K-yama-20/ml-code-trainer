import type { Result } from "../types/domain";
import { ResultValue } from "./ResultValue";

export function hasActualValue(
  first: NonNullable<Result["tests"]>[number] | undefined,
  verdict: string,
): first is NonNullable<Result["tests"]>[number] & { actual: unknown } {
  const executionError = verdict !== "Accepted" && verdict !== "Wrong Answer";
  // Older server errors stored actual=null even when Python returned no value.
  return Boolean(
    first &&
    "actual" in first &&
    first.actual !== undefined &&
    !(executionError && first.error && first.actual === null),
  );
}

export function ComputedResult({ result }: { result: Result }) {
  const first = result.tests?.[0];
  const executionError =
    result.verdict !== "Accepted" && result.verdict !== "Wrong Answer";
  const hasValue = hasActualValue(first, result.verdict);

  if (!hasValue && (executionError || first?.error)) return null;
  return (
    <div className="computed-result" role="group" aria-label="result">
      <h4>result</h4>
      {hasValue ? (
        <ResultValue
          value={first.actual}
          tuplePaths={first.actual_tuple_paths}
          warnMissingTupleTypes
          checkDtype
        />
      ) : (
        <p>この保存結果には実値がありません。再実行すると確認できます。</p>
      )}
    </div>
  );
}
