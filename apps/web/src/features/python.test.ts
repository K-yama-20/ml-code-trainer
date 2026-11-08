import { describe, expect, it } from "vitest";
import { equivalent } from "./python";
describe("public result comparison", () => {
  it("accepts float tolerance and NaN markers", () => {
    expect(equivalent([1.000001, "__NaN__"], [1, "__NaN__"])).toBe(true);
  });
  it("rejects incorrect shapes and strict dtype", () => {
    expect(equivalent({ shape: [2, 1] }, { shape: [2] })).toBe(false);
    expect(equivalent({ dtype: "int64" }, { dtype: "float32" }, true)).toBe(
      false,
    );
  });
  it("distinguishes boolean and numeric output", () => {
    expect(equivalent(true, 1)).toBe(false);
    expect(equivalent(0, false)).toBe(false);
  });
  it("compares nested tensors and pandas data", () => {
    expect(
      equivalent(
        { kind: "tensor", shape: [2], data: [1, 2], dtype: "torch.float32" },
        { kind: "tensor", shape: [2], data: [1, 2], dtype: "torch.float64" },
      ),
    ).toBe(true);
    expect(equivalent({ data: [1, 2] }, { data: [1, 3] })).toBe(false);
  });
  it("uses JSON semantics only when requested and preserves Unicode requirements", () => {
    const expected = '{"name":"画像分類","epochs":2}';
    const reordered = '{ "epochs": 2, "name": "画像分類" }';
    expect(equivalent(reordered, expected, true, "json")).toBe(true);
    expect(equivalent(reordered, expected, true)).toBe(false);
    expect(
      equivalent({ name: "画像分類", epochs: 2 }, expected, true, "json"),
    ).toBe(false);
    const escaped = '{"name":"\\u753b\\u50cf\\u5206\\u985e","epochs":2}';
    expect(equivalent(escaped, expected, true, "json")).toBe(true);
    expect(equivalent(escaped, expected, true, "json_unicode")).toBe(false);
    expect(equivalent(reordered, expected, true, "json_unicode")).toBe(true);
  });
});
