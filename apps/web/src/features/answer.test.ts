import { expect, test } from "vitest";
import { answerCode, readAnswer, outputDescription } from "./answer";
import type { Problem } from "../types/domain";
const p = {
  starter_code: "def solve(a, b):\n    return ___\n",
  public_tests: [{ expected: { kind: "array" } }],
} as Problem;
test("legacy output copy adds a type without fixing the shape of a general problem", () => {
  const q = {
    ...p,
    module_id: "numpy",
    description: "各列の総和を返す。",
    output_conditions: "各列の総和を返す。",
    public_tests: [
      { expected: { kind: "array", shape: [4], data: [1, 2, 3, 4] } },
    ],
  } as Problem;
  expect(outputDescription(q)).toContain("NumPy配列");
  expect(outputDescription(q)).not.toContain("4");
  expect(outputDescription(q)).not.toBe(q.description);
});

test("a prediction is saved as the exact learner expression in an executable function", () => {
  const code = answerCode(p, "[[3,4],\n [6,8]]");
  expect(code).toContain("def solve(a, b):\n    return np.asarray((");
  expect(code).toContain("        [[3,4],\n         [6,8]]");
  expect(readAnswer(p, code)).toBe("[[3,4],\n [6,8]]");
});
test("existing code drafts are preserved instead of being converted to a blank prediction", () => {
  expect(
    readAnswer(p, "def solve(a, b):\n    print(a)\n    return a[:,None]*b"),
  ).toBeNull();
  expect(readAnswer(p, p.starter_code)).toBe("");
});

test("concrete array predictions preserve the shown dtype without requiring array construction", () => {
  const q = {
    ...p,
    workspace: { mode: "prediction" },
    public_tests: [{ expected: { kind: "array", dtype: "float64" } }],
  } as Problem;
  const code = answerCode(q, "[[7, 7], [7, 7]]");
  expect(code).toContain('dtype="float64"');
  expect(readAnswer(q, code)).toBe("[[7, 7], [7, 7]]");
});
