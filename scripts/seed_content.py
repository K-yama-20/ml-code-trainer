# ruff: noqa: E402
"""Idempotently sync Git-authored content, preserving old versions and histories."""

import json
from pathlib import Path
import sys
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apps.api.app.config import settings
from apps.api.app.content import DATA, public_activity, public_problem, reading_projects
from apps.api.app.db import engine
from content.activities import DEEP_DIVES


def main():
    if not settings.database_url.startswith("postgresql"):
        raise SystemExit(
            "Seed sync targets migrated PostgreSQL. Local SQLite reads the compiled Git catalog directly."
        )
    with engine.begin() as db:

        def upsert(table, id, data, **fields):
            params = {"id": id, "data": json.dumps(data, ensure_ascii=False), **fields}
            columns = ",".join(params)
            values = ",".join(
                "cast(:data as jsonb)" if k == "data" else ":" + k for k in params
            )
            updates = ",".join(f"{k}=excluded.{k}" for k in params if k != "id")
            db.execute(
                text(
                    f"INSERT INTO {table} ({columns}) VALUES ({values}) ON CONFLICT(id) DO UPDATE SET {updates}"
                ),
                params,
            )

        for m in DATA["modules"]:
            upsert("curriculum_modules", m["id"], m)
        for c in DATA["concepts"]:
            upsert("concepts", c["id"], c, module_id=c["module_id"])
        for c in DATA["concepts"]:
            for prerequisite in c["prerequisites"]:
                db.execute(
                    text(
                        "INSERT INTO concept_prerequisites VALUES (:c,:p) ON CONFLICT DO NOTHING"
                    ),
                    {"c": c["id"], "p": prerequisite},
                )
        for p in DATA["problems"]:
            upsert(
                "problem_families",
                p["id"],
                {"title": p["title"], "stage": p["stage"]},
                concept_id=p["concept_id"],
            )
            # A changed released version is rejected. Increment content_version instead.
            previous = db.execute(
                text("SELECT data FROM problem_versions WHERE id=:id"),
                {"id": p["version_id"]},
            ).scalar()
            public = public_problem(p)
            if previous is not None and previous != public:
                raise RuntimeError(f"Published version is immutable: {p['version_id']}")
            upsert(
                "problem_versions",
                p["version_id"],
                public,
                family_id=p["id"],
                version=p["content_version"],
            )
            db.execute(
                text(
                    "INSERT INTO private.grader_test_sets VALUES (:id,cast(:data as jsonb)) ON CONFLICT(problem_version_id) DO NOTHING"
                ),
                {
                    "id": p["version_id"],
                    "data": json.dumps(
                        {"hidden_tests": p["hidden_tests"], "solution": p["solution"]}
                    ),
                },
            )
        for a in DEEP_DIVES:
            upsert("deep_dive_tasks", a["id"], public_activity(a))
            upsert("private.activity_answers", a["id"], a["questions"])
        for a in reading_projects():
            upsert("reading_projects", a["id"], public_activity(a))
            for q in a["questions"]:
                upsert(
                    "reading_questions",
                    q["id"],
                    {k: v for k, v in q.items() if k not in ("answer", "explanation")},
                    project_id=a["id"],
                )
            upsert("private.activity_answers", a["id"], a["questions"])
    print(f"Synced {len(DATA['concepts'])} concepts, {len(DATA['problems'])} problem versions, 12 Deep Dives, 3 reading projects")


if __name__ == "__main__":
    main()
