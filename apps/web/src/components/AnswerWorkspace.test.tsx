import publicCatalog from "../../../../content/compiled/public.json?raw";
import { expect, test, vi } from "vitest";
import { answerLayout, needsAnswer } from "./AnswerWorkspace";
import type { Problem } from "../types/domain";
vi.mock("./CodeEditor", () => ({ CodeEditor: () => null }));
const p = {
  stage: "guided",
  starter_code: "result = x.mean(axis=___)\n",
  workspace: { provided_code: "x = np.array([[1,3],[5,7]])" },
} as Problem;
test("Guided has exactly one editable span inside a unified document", () => {
  const l = answerLayout(p, p.starter_code);
  expect(l.prefix).toContain("x = np.array");
  expect(l.prefix).toContain("result = x.mean(axis=");
  expect(l.suffix).toBe(")\n");
  expect(l.value).toBe("");
  expect(l.encode("")).toBe("result = x.mean(axis=)\n");
  expect(needsAnswer(p, l.encode(""))).toBe(true);
  expect(l.encode("1")).toBe("result = x.mean(axis=1)\n");
});
test("nonstandard saved answers retain their code", () => {
  const c = "result=np.sum(x,axis=1)/2";
  expect(answerLayout(p, c).value).toBe(c);
});

test("all coding starter templates round-trip without mixing fixtures into saved code", async () => {
  const ps = JSON.parse(publicCatalog).problems;
  for (const p of ps) {
    if (p.type === "prediction") continue;
    for (const code of [p.starter_code]) {
      const l = answerLayout(p, code);
      const decoded = answerLayout(p, l.encode(l.value));
      expect(decoded.value, p.id).toBe(l.value);
      expect(decoded.prefix, p.id).toBe(l.prefix);
      expect(l.value, p.id).not.toContain("___");
      expect(l.prefix).toContain(p.workspace.provided_code);
    }
  }
});

test("archived function drafts retain the full editable range without a placeholder", () => {
  const legacy = {
    ...p,
    workspace: undefined,
    starter_code: "def solve(x):\n    return ___\n",
  };
  const layout = answerLayout(legacy, legacy.starter_code);
  expect(layout.prefix).toBe("");
  expect(layout.suffix).toBe("");
  expect(layout.value).toBe("def solve(x):\n    return \n");
  expect(layout.cursorOffset).toBe(layout.value.length - 1);
  expect(needsAnswer(legacy, layout.value)).toBe(true);
  const solution = "def solve(x):\n    return x.mean(axis=1)\n";
  expect(layout.encode(solution)).toBe(solution);
  expect(needsAnswer(legacy, solution)).toBe(false);
});
