import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig(({ mode }) => ({
  envDir: "../..",
  plugins: [react(), tailwindcss()],
  // The SQLite loader resolves its Wasm next to the module in development.
  optimizeDeps: { exclude: ["@sqlite.org/sqlite-wasm"] },
  server: {
    proxy: {
      "/api":
        loadEnv(mode, "../..", "API_").API_PROXY_TARGET ??
        "http://127.0.0.1:8000",
    },
  },
  test: { environment: "jsdom", setupFiles: ["./src/test-setup.ts"] },
  build: { chunkSizeWarningLimit: 3000 },
}));
