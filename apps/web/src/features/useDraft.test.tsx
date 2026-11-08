import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useDraft } from "./useDraft";
const { save, write } = vi.hoisted(() => ({ save: vi.fn(), write: vi.fn() }));
vi.mock("../lib/api", () => ({ userApi: save }));
vi.mock("../lib/drafts", () => ({ writeLocal: write }));
beforeEach(() => {
  vi.useFakeTimers();
  save.mockReset();
  write.mockReset();
  write.mockResolvedValue(undefined);
});
afterEach(() => vi.useRealTimers());
it("saves a restored dirty draft and syncs its revision", async () => {
  save.mockResolvedValue({ revision: 3 });
  const { result } = renderHook(() =>
    useDraft("user-a", "item-a", "restored code", 2, "older code"),
  );
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1100);
  });
  expect(write).toHaveBeenCalledWith(
    "user-a",
    "item-a",
    expect.objectContaining({ code: "restored code", dirty: true }),
  );
  await act(async () => {
    await vi.advanceTimersByTimeAsync(4000);
  });
  expect(save).toHaveBeenCalledWith(
    "/drafts/item-a",
    expect.objectContaining({
      body: JSON.stringify({ code: "restored code", revision: 2 }),
    }),
  );
  expect(result.current.code).toBe("restored code");
});
it("preserves edits on a server revision conflict", async () => {
  save.mockRejectedValue(Object.assign(new Error("conflict"), { status: 409 }));
  const { result } = renderHook(() =>
    useDraft("user-b", "item-b", "initial", 0),
  );
  await act(async () => {
    result.current.setCode("keep this code");
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5100);
  });
  expect(result.current.code).toBe("keep this code");
  expect(result.current.status).toContain("競合");
});
