import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import { ResultValue } from "./ResultValue";
import { ComputedResult } from "./ComputedResult";
import type { Result } from "../types/domain";
import type { TuplePaths } from "../types/domain";

afterEach(cleanup);

test.each<{ value: unknown; paths: TuplePaths; text: string }>([
  {
    value: [
      [0.1, 16],
      [0.1, 32],
    ],
    paths: [[0], [1]],
    text: "[(0.1, 16), (0.1, 32)]",
  },
  {
    value: [
      [0.1, 16],
      [0.1, 32],
    ],
    paths: [],
    text: "[[0.1, 16], [0.1, 32]]",
  },
  { value: [], paths: [], text: "[]" },
  { value: [], paths: [[]], text: "()" },
  { value: [7], paths: [], text: "[7]" },
  { value: [7], paths: [[]], text: "(7,)" },
  {
    value: [
      [1, 2],
      [3, 4],
    ],
    paths: [[], [1]],
    text: "([1, 2], (3, 4))",
  },
  {
    value: { kind: "tuple", tuple_paths: [[0]], value: [[7]] },
    paths: [["value", 0]],
    text: '{"kind": "tuple", "tuple_paths": [[0]], "value": [(7,)]}',
  },
  { value: [[[[7]]]], paths: [[], [0, 0, 0]], text: "([[(7,)]],)" },
])(
  "renders the complete Python value $text using separate type paths",
  ({ value, paths, text }) => {
    const { container } = render(
      <ResultValue value={value} tuplePaths={paths} />,
    );
    expect(container.querySelector(".value-data")?.textContent).toBe(text);
  },
);

test.each(["Accepted", "Wrong Answer"])(
  "%s keeps actual tuple types, independently of expected",
  (verdict) => {
    const result: Result = {
      verdict,
      passed_tests: 0,
      total_tests: 1,
      tests: [
        {
          name: "first",
          passed: false,
          actual: [[7]],
          actual_tuple_paths: [[0]],
          expected: [[99]],
          expected_tuple_paths: [[]],
        },
      ],
    };
    const { container } = render(<ComputedResult result={result} />);
    expect(container.querySelector(".value-data")?.textContent).toBe("[(7,)]");
    expect(screen.queryByText(/99/)).not.toBeInTheDocument();
  },
);

test("old JSON values are never guessed to be tuples", () => {
  const result: Result = {
    verdict: "Accepted",
    passed_tests: 1,
    total_tests: 1,
    tests: [{ name: "first", passed: true, actual: [[7]] }],
  };
  const { container, rerender } = render(<ComputedResult result={result} />);
  expect(container.querySelector(".value-data")?.textContent).toBe("[[7]]");
  expect(
    screen.getByText(/この保存結果には型情報がありません/),
  ).toBeInTheDocument();
  result.tests![0].actual_tuple_paths = [];
  rerender(<ComputedResult result={result} />);
  expect(
    screen.queryByText(/この保存結果には型情報がありません/),
  ).not.toBeInTheDocument();
});

test("Pandas output keeps the graded index, columns and missing values visible", () => {
  render(
    <ResultValue
      value={{
        kind: "dataframe",
        columns: ["score"],
        index: [3, 7],
        data: [[5], ["__NaN__"]],
      }}
    />,
  );
  expect(
    screen.getByRole("columnheader", { name: "index" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("columnheader", { name: "score" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("rowheader", { name: "7" })).toBeInTheDocument();
  expect(screen.getByText("NaN（欠損）")).toBeInTheDocument();
});
test.each([
  { label: "0D", shape: [], data: 1.28, text: "1.28", metadata: "shape ()" },
  {
    label: "1D",
    shape: [3],
    data: [1, 2, 3],
    text: "[1, 2, 3]",
    metadata: "shape (3,)",
  },
  {
    label: "2D",
    shape: [2, 3],
    data: [
      [1, 2, 3],
      [4, 5, 6],
    ],
    text: "[[1, 2, 3], [4, 5, 6]]",
    metadata: "shape (2, 3)",
  },
  {
    label: "3D",
    shape: [1, 2, 3],
    data: [
      [
        [1, 2, 3],
        [4, 5, 6],
      ],
    ],
    text: "[[[1, 2, 3], [4, 5, 6]]]",
    metadata: "shape (1, 2, 3)",
  },
  {
    label: "4D",
    shape: [1, 1, 1, 2],
    data: [[[[1, 2]]]],
    text: "[[[[1, 2]]]]",
    metadata: "shape (1, 1, 1, 2)",
  },
  {
    label: "empty outer axis",
    shape: [0, 4],
    data: [],
    text: "[]",
    metadata: "shape (0, 4)",
  },
  {
    label: "empty inner axis",
    shape: [2, 0],
    data: [[], []],
    text: "[[], []]",
    metadata: "shape (2, 0)",
  },
  {
    label: "zero and NaN",
    shape: [1, 2],
    data: [[0, "__NaN__"]],
    text: "[[0, NaN（欠損）]]",
    metadata: "shape (1, 2)",
  },
  {
    label: "booleans",
    shape: [1, 2],
    data: [[false, true]],
    text: "[[False, True]]",
    metadata: "shape (1, 2)",
    dtype: "bool",
  },
])(
  "array $label keeps its complete value, shape and dtype",
  ({ shape, data, text, metadata, dtype }) => {
    const actualDtype = dtype ?? "float32";
    const { container } = render(
      <ResultValue
        checkDtype
        value={{
          kind: "array",
          shape,
          data,
          dtype: actualDtype,
        }}
      />,
    );
    expect(container.querySelector(".value-data")?.textContent).toBe(text);
    expect(container.querySelector(".value-shape")?.textContent).toBe(
      `${metadata} · dtype ${actualDtype}`,
    );
  },
);

test.each(["Accepted", "Wrong Answer"])(
  "the %s result shows only the first public actual value",
  (verdict) => {
    render(
      <ComputedResult
        result={{
          verdict,
          passed_tests: 1,
          total_tests: 3,
          tests: [
            {
              name: "public",
              passed: false,
              actual: {
                kind: "array",
                data: [8, 5, 10, 5],
                shape: [4],
                dtype: "int64",
              },
              expected: "expected-only",
            },
            { name: "other", passed: true, actual: "other-case-value" },
          ],
        }}
      />,
    );
    expect(screen.getByRole("group", { name: "result" })).toHaveTextContent(
      "[8, 5, 10, 5]",
    );
    expect(screen.getByText(/shape \(4,\)/)).toHaveTextContent("dtype int64");
    expect(screen.queryByText("expected-only")).not.toBeInTheDocument();
    expect(screen.queryByText("other-case-value")).not.toBeInTheDocument();
  },
);

test("zero, False, an empty array and a returned None are actual results", () => {
  const result: Result = {
    verdict: "Accepted",
    passed_tests: 1,
    total_tests: 1,
  };
  const { rerender } = render(<ComputedResult result={result} />);
  for (const [actual, text] of [
    [0, "0"],
    [false, "False"],
    [{ kind: "array", data: [], shape: [0], dtype: "float64" }, "[]"],
    [null, "None"],
  ] as const) {
    rerender(
      <ComputedResult
        result={{ ...result, tests: [{ name: "first", passed: true, actual }] }}
      />,
    );
    expect(screen.getByText(text)).toBeInTheDocument();
    expect(screen.queryByText(/再実行すると/)).not.toBeInTheDocument();
  }
});

test("runtime errors never turn a missing value or a legacy null into None", () => {
  const result: Result = {
    verdict: "Runtime Error",
    passed_tests: 0,
    total_tests: 1,
  };
  const { rerender } = render(<ComputedResult result={result} />);
  for (const first of [
    { name: "first", passed: false, error: "NameError" },
    { name: "first", passed: false, error: "NameError", actual: null },
    { name: "first", passed: false, error: "NameError", actual: undefined },
  ]) {
    rerender(<ComputedResult result={{ ...result, tests: [first] }} />);
    expect(
      screen.queryByRole("group", { name: "result" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("None")).not.toBeInTheDocument();
  }
});

test("a saved verdict without actual values offers a rerun", () => {
  render(
    <ComputedResult
      result={{ verdict: "Accepted", passed_tests: 2, total_tests: 2 }}
    />,
  );
  expect(screen.getByText(/再実行すると確認できます/)).toBeInTheDocument();
  expect(screen.queryByText("None")).not.toBeInTheDocument();
});
