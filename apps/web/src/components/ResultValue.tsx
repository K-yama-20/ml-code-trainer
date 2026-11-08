import type { TuplePaths } from "../types/domain";

function literal(
  value: unknown,
  tuples: TuplePaths = [],
  path: (string | number)[] = [],
): string {
  if (value === "__NaN__") return "NaN（欠損）";
  if (value === "__Inf__" || value === "__-Inf__")
    return value === "__Inf__" ? "∞" : "−∞";
  if (value === null) return "None";
  if (typeof value === "boolean") return value ? "True" : "False";
  if (typeof value === "number") return String(Number(value.toPrecision(7)));
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) {
    const items = value
      .map((item, i) => literal(item, tuples, [...path, i]))
      .join(", ");
    const isTuple = tuples.some(
      (p) => p.length === path.length && p.every((part, i) => part === path[i]),
    );
    return isTuple
      ? `(${items}${value.length === 1 ? "," : ""})`
      : `[${items}]`;
  }
  if (
    value &&
    typeof value === "object" &&
    "kind" in value &&
    value.kind === "path" &&
    "value" in value
  )
    return `Path(${JSON.stringify(value.value)})`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .map(
        ([k, v]) => `${JSON.stringify(k)}: ${literal(v, tuples, [...path, k])}`,
      )
      .join(", ")}}`;
  return "値を取得できませんでした";
}
function hasUntypedSequence(value: unknown): boolean {
  if (Array.isArray(value)) return true;
  if (!value || typeof value !== "object") return false;
  if (
    "kind" in value &&
    ["array", "tensor", "dataframe", "series", "path"].includes(
      String(value.kind),
    )
  )
    return false;
  return Object.values(value).some(hasUntypedSequence);
}

export function ResultValue({
  value,
  checkDtype = false,
  tuplePaths,
  warnMissingTupleTypes = false,
}: {
  value: unknown;
  checkDtype?: boolean;
  tuplePaths?: TuplePaths | null;
  warnMissingTupleTypes?: boolean;
}) {
  const tuples = tuplePaths ?? [];
  if (
    value &&
    typeof value === "object" &&
    "kind" in value &&
    "data" in value
  ) {
    const v = value as {
      kind: string;
      data: unknown;
      columns?: string[];
      index?: unknown[];
      shape?: number[];
      dtype?: string;
    };
    if (
      (v.kind === "dataframe" || v.kind === "series") &&
      Array.isArray(v.data)
    )
      return (
        <div className="value-scroll">
          <table className="result-table">
            <thead>
              <tr>
                <th>index</th>
                {(v.columns ?? ["値"]).map((c) => (
                  <th key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {v.data.map((row, i) => (
                <tr key={i}>
                  <th scope="row">
                    {literal(v.index?.[i], tuples, ["index", i])}
                  </th>
                  {(Array.isArray(row) && v.kind === "dataframe"
                    ? row
                    : [row]
                  ).map((cell, j) => (
                    <td key={j}>
                      {literal(
                        cell,
                        tuples,
                        v.kind === "dataframe" ? ["data", i, j] : ["data", i],
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    return (
      <div>
        <small className="value-shape">
          shape ({v.shape?.join(", ")}
          {v.shape?.length === 1 ? "," : ""})
          {checkDtype && v.dtype && ` · dtype ${v.dtype}`}
        </small>
        <pre className="value-data">{literal(v.data, tuples, ["data"])}</pre>
      </div>
    );
  }
  return (
    <>
      <pre className="value-data">{literal(value, tuples)}</pre>
      {warnMissingTupleTypes &&
        tuplePaths == null &&
        hasUntypedSequence(value) && (
          <small>
            この保存結果には型情報がありません。再実行するとリストとタプルを区別して表示できます。
          </small>
        )}
    </>
  );
}
