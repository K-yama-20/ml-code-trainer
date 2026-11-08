import { create } from "zustand";
import { persist } from "zustand/middleware";
interface UIState {
  focus: boolean;
  split: number;
  resultHeight: number;
  resultTab: string;
  setFocus: (v: boolean) => void;
  setSplit: (v: number) => void;
  setResultHeight: (v: number) => void;
  setResultTab: (v: string) => void;
}
export const useUI = create<UIState>()(
  persist(
    (set) => ({
      focus: false,
      split: 35,
      resultHeight: 240,
      resultTab: "tests",
      setFocus: (v) => set({ focus: v }),
      setSplit: (v) => set({ split: v }),
      setResultHeight: (v) => set({ resultHeight: v }),
      setResultTab: (v) => set({ resultTab: v }),
    }),
    { name: "ml-trainer-ui" },
  ),
);
