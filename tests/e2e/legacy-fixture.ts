import { execFileSync } from "node:child_process";

// Exercise historical sessions on the dedicated QA database. No production DB
// or API accepts a client-supplied problem version or execution definition.
export function historicalSession(sessionId: string) {
  if (!process.env.LEGACY_QA_DB) return;
  if (
    !process.env.LEGACY_QA_DB.replaceAll("\\", "/").includes(
      "artifacts/concrete-drill/",
    )
  )
    throw new Error("Expected isolated QA database");
  execFileSync(
    process.env.TRAINER_QA_PYTHON || "apps/api/.venv/Scripts/python.exe",
    [
      "-c",
      `
import sqlite3,sys
db=sqlite3.connect(sys.argv[1])
db.execute("UPDATE session_items SET problem_version_id=substr(problem_version_id,1,instr(problem_version_id,'@')) || '1' WHERE session_id=?",(sys.argv[2],))
db.commit()
`,
      process.env.LEGACY_QA_DB,
      sessionId,
    ],
  );
}

export function pinProblemVersion(itemId: string, versionId: string) {
  const db = process.env.LEGACY_QA_DB;
  if (!db?.replaceAll("\\", "/").includes("artifacts/concrete-drill/"))
    throw new Error("Expected isolated QA database");
  execFileSync(
    process.env.TRAINER_QA_PYTHON || "apps/api/.venv/Scripts/python.exe",
    [
      "-c",
      'import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); db.execute("UPDATE session_items SET problem_version_id=? WHERE id=?", (sys.argv[3], sys.argv[2])); db.commit()',
      db,
      itemId,
      versionId,
    ],
  );
}
