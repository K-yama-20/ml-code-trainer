import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";
import { mkdirSync } from "node:fs";
mkdirSync(resolve("artifacts/concrete-drill"), { recursive: true });
const webPort = Number(process.env.TRAINER_QA_WEB_PORT ?? 5174);
const apiPort = Number(process.env.TRAINER_QA_API_PORT ?? 8001);
process.env.LEGACY_QA_DB = resolve(
  `artifacts/concrete-drill/e2e-${apiPort}.db`,
);
process.env.TRAINER_QA_PYTHON =
  process.platform === "win32"
    ? "apps/api/.venv/Scripts/python.exe"
    : "apps/api/.venv/bin/python";
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch:
    /(unified|trainer|prediction|browser-content|editor-regression|runtime-regression|iteration|shortcuts|arguments|files|workspace-drawer)\.spec\.ts/,
  workers: 1,
  timeout: 360000,
  expect: { timeout: 15000 },
  reporter: [["list"]],
  outputDir: "artifacts/concrete-drill/e2e-results",
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `npm run dev -w apps/web -- --port ${webPort} --strictPort`,
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
      env: {
        API_PROXY_TARGET: `http://127.0.0.1:${apiPort}`,
        VITE_SUPABASE_URL: "",
        VITE_SUPABASE_ANON_KEY: "",
      },
    },
    {
      command: `"${resolve(process.env.TRAINER_QA_PYTHON)}" -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port ${apiPort}`,
      url: `http://127.0.0.1:${apiPort}/api/v1/health`,
      reuseExistingServer: false,
      env: {
        DATABASE_URL: `sqlite:///${process.env.LEGACY_QA_DB.replaceAll("\\", "/")}`,
        WEB_ORIGIN: `http://127.0.0.1:${webPort}`,
        EXECUTION_PROVIDER: "disabled",
        SUPABASE_URL: "",
      },
    },
  ],
});
