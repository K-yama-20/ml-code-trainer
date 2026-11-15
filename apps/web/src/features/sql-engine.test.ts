import { expect, test } from "vitest";
import { sameTable } from "./sql-engine";
import type { SqlCell } from "../types/domain";

const table = (rows: SqlCell[][], columns = ["x"]) => ({ rows, columns });
const compare = (
  actual: ReturnType<typeof table>,
  expected: ReturnType<typeof table>,
  options = {},
) =>
  sameTable(
    actual,
    expected,
    { ordered: false, column_names: false, approximate: false, ...options },
    1e-8,
  );

test("unordered results preserve duplicates and keep NULL, empty text and zero distinct", () => {
  const expected = table([[null], [""], [0], [null]]);
  expect(compare(table([[0], [null], [null], [""]]), expected)).toBe(true);
  expect(compare(table([[0], [null], [0], [""]]), expected)).toBe(false);
  expect(compare(table([[0], [null], ["0"], [null]]), expected)).toBe(false);
});

test("row order and headings are optional, column count and order are required", () => {
  const expected = table(
    [
      [1, 2],
      [3, 4],
    ],
    ["a", "b"],
  );
  const reordered = table(
    [
      [3, 4],
      [1, 2],
    ],
    ["a", "b"],
  );
  expect(compare(reordered, expected)).toBe(true);
  expect(compare(reordered, expected, { ordered: true })).toBe(false);
  expect(
    compare(
      table(
        [
          [1, 2],
          [3, 4],
        ],
        ["a", "c"],
      ),
      expected,
      { column_names: true },
    ),
  ).toBe(false);
  expect(
    compare(
      table(
        [
          [2, 1],
          [4, 3],
        ],
        ["b", "a"],
      ),
      expected,
    ),
  ).toBe(false);
  expect(compare(table([[1], [3]]), expected)).toBe(false);
});

test("approximate matching accepts nearby aggregates without rounding or reusing rows", () => {
  const expected = table([[0], [1.5e-8]]);
  const actual = table([[0.75e-8], [0]]);
  expect(compare(actual, expected)).toBe(false);
  expect(compare(actual, expected, { approximate: true })).toBe(true);
  expect(compare(table([[0], [0]]), expected, { approximate: true })).toBe(
    false,
  );
});
