import type { Problem } from "../types/domain";

export function signature(p: Problem) {
  return p.starter_code.match(/^def \w+\([^\n]*\):/m)?.[0] ?? "def solve():";
}
function predictionFrame(p: Problem) {
  const first = p.public_tests[0]?.expected;
  const array =
    p.presentation?.answer?.wrap_array ??
    (!!first &&
      typeof first === "object" &&
      "kind" in first &&
      first.kind === "array");
  const dtype =
    array &&
    p.workspace?.mode === "prediction" &&
    first &&
    typeof first === "object" &&
    "dtype" in first &&
    typeof first.dtype === "string"
      ? `, dtype=${JSON.stringify(first.dtype)}`
      : "";
  return {
    prefix: `# trainer:prediction-answer\n${signature(p)}\n    return ${array ? "np.asarray((" : "("}\n`,
    suffix: `\n    ${array ? `)${dtype})` : ")"}\n`,
  };
}
export function answerCode(p: Problem, answer: string) {
  const { prefix, suffix } = predictionFrame(p);
  return (
    prefix +
    (answer || "___")
      .split("\n")
      .map((s) => "        " + s)
      .join("\n") +
    suffix
  );
}
export function readAnswer(p: Problem, code: string): string | null {
  if (code === p.starter_code) return "";
  const { prefix, suffix } = predictionFrame(p);
  if (!code.startsWith(prefix) || !code.endsWith(suffix)) return null;
  const value = code
    .slice(prefix.length, -suffix.length)
    .split("\n")
    .map((s) => s.slice(8))
    .join("\n");
  return value === "___" ? "" : value;
}
export function editInstruction(p: Problem) {
  if (p.presentation) return p.presentation.edit_instruction;
  if (p.type === "prediction")
    return "戻り値だけを入力します。入力に応じる場合は引数名を使ったPythonの式で答えてください。関数の定義は不要です。";
  if (p.type === "bugfix")
    return "初期コードの処理を修正してください。関数名と引数はそのまま使います。";
  if (p.type === "implementation")
    return "solveの中に処理を書き、passを置き換えます。結果はprintではなくreturnで返します。";
  return p.stage === "guided"
    ? "強調された___を埋めます。関数名と引数は変えません。"
    : "return ___を必要な処理に置き換えます。結果はreturnで返してください。";
}
export function outputDescription(p: Problem) {
  if (p.workspace && !p.workspace.authored && p.workspace.mode === "script") {
    const expected = p.public_tests[0]?.expected;
    if (expected && typeof expected === "object" && "kind" in expected) {
      const kinds: Record<string, string> = {
        array: "NumPy配列",
        tensor: "Tensor",
        dataframe: "DataFrame（表）",
        series: "Series（1列のデータ）",
      };
      const kind = kinds[String(expected.kind)];
      return `resultに${kind ?? "処理結果"}を代入します。`;
    }
    return `resultに${Array.isArray(expected) ? "リストまたはタプル" : typeof expected === "boolean" ? "TrueまたはFalse" : typeof expected === "number" ? "計算した数値" : "処理した値"}を代入します。`;
  }
  if (p.presentation || p.output_conditions !== taskText(p))
    return p.output_conditions;
  // Legacy copy repeats the task. Infer only the type, never a fixed shape.
  const expected = p.public_tests[0]?.expected;
  if (expected && typeof expected === "object" && "kind" in expected) {
    if (expected.kind === "array")
      return `${p.module_id === "pytorch" ? "Tensor" : "NumPy配列"}。値の順序と次元は、問題文の条件に合わせてください。`;
    if (expected.kind === "dataframe")
      return "DataFrame（表）。列と行ラベルは、問題文の条件に合わせてください。";
    if (expected.kind === "series") return "Series（行ラベル付きの1列）。";
  }
  if (Array.isArray(expected))
    return p.type === "prediction" && p.output_conditions.includes("shape")
      ? "shapeを表すタプル。入力に応じて変わる場合は、引数を使った式で答えてください。"
      : "リストまたはタプル。要素の順序は問題文の指定に合わせます。";
  if (typeof expected === "number") return "計算で求めた数値を返してください。";
  if (typeof expected === "boolean")
    return "TrueまたはFalseの真偽値を返してください。文字列ではありません。";
  if (typeof expected === "string")
    return "文字列を返してください。printによる表示ではなく、戻り値で答えます。";
  return "処理の結果をPythonの値として返してください。";
}

export function taskText(p: Problem) {
  if (p.workspace) return p.workspace.task;
  return p.description
    .replace(
      /^次の処理の戻り値を予測してください。solve内で同等の値を返します。\s*/,
      "",
    )
    .replace(/^初期コードのBUGを修正し、次の条件を満たしてください。\s*/, "");
}
