import base from "./playwright.concrete.config";
export default {
  ...base,
  testMatch: /runtime-performance\.spec\.ts/,
  outputDir: "artifacts/runtime-performance",
};
