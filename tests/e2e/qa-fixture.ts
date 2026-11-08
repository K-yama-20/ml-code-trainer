import { test as base } from "@playwright/test";
import { execFileSync } from "node:child_process";
export { expect } from "@playwright/test";
export type { Page } from "@playwright/test";

export const test = base.extend<{ isolatedGuestBudget: void }>({
  isolatedGuestBudget: [
    async ({}, use) => {
      const db = process.env.LEGACY_QA_DB;
      if (db) {
        if (!db.replaceAll("\\", "/").includes("artifacts/concrete-drill/"))
          throw new Error("Expected isolated QA database");
        // Each test is a different learner. Reset only the shared localhost guest
        // creation budget; production limits and user/session quotas stay intact.
        execFileSync(
          process.env.TRAINER_QA_PYTHON || "apps/api/.venv/Scripts/python.exe",
          [
            "-c",
            "import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); db.execute(\"DELETE FROM system_usage_daily WHERE key LIKE 'guest-ip:%'\"); db.commit()",
            db,
          ],
        );
      }
      await use();
    },
    { auto: true },
  ],
});
