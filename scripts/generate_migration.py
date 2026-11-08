# ruff: noqa: E402
"""Rebuild the initial migration before the first deployment only."""

from pathlib import Path
import sys
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.dialects import postgresql

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from apps.api.app.db import Base


def generate():
    dialect = postgresql.dialect()
    parts = [
        "-- ML Code Trainer / Supabase PostgreSQL. Apply once with Supabase migrations.\nBEGIN;"
    ]
    for table in Base.metadata.sorted_tables:
        parts.append(str(CreateTable(table).compile(dialect=dialect)) + ";")
        for index in table.indexes:
            parts.append(str(CreateIndex(index).compile(dialect=dialect)) + ";")
    parts.append("""
CREATE TABLE curriculum_modules (id text PRIMARY KEY, data jsonb NOT NULL);
CREATE TABLE concepts (id text PRIMARY KEY, module_id text NOT NULL REFERENCES curriculum_modules(id), data jsonb NOT NULL);
CREATE TABLE concept_prerequisites (concept_id text REFERENCES concepts(id), prerequisite_id text REFERENCES concepts(id), PRIMARY KEY(concept_id,prerequisite_id));
CREATE TABLE problem_families (id text PRIMARY KEY, concept_id text NOT NULL REFERENCES concepts(id), data jsonb NOT NULL);
CREATE TABLE problem_versions (id text PRIMARY KEY, family_id text NOT NULL REFERENCES problem_families(id), version integer NOT NULL, data jsonb NOT NULL, UNIQUE(family_id,version));
CREATE TABLE deep_dive_tasks (id text PRIMARY KEY, data jsonb NOT NULL);
CREATE TABLE reading_projects (id text PRIMARY KEY, data jsonb NOT NULL);
CREATE TABLE reading_questions (id text PRIMARY KEY, project_id text NOT NULL REFERENCES reading_projects(id), data jsonb NOT NULL);
ALTER TABLE user_problem_progress ADD CONSTRAINT progress_version_fk FOREIGN KEY(problem_version_id) REFERENCES problem_versions(id);
CREATE SCHEMA IF NOT EXISTS private;
REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated;
CREATE TABLE private.grader_test_sets (problem_version_id text PRIMARY KEY REFERENCES problem_versions(id), data jsonb NOT NULL);
CREATE TABLE private.activity_answers (id text PRIMARY KEY, data jsonb NOT NULL);
REVOKE ALL ON ALL TABLES IN SCHEMA private FROM PUBLIC, anon, authenticated;
ALTER TABLE private.grader_test_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE private.activity_answers ENABLE ROW LEVEL SECURITY;
-- API/worker connect with a dedicated trusted DB role; browser roles cannot write certification.
""")
    public = [
        "curriculum_modules",
        "concepts",
        "concept_prerequisites",
        "problem_families",
        "problem_versions",
        "deep_dive_tasks",
        "reading_projects",
        "reading_questions",
    ]
    for table in public:
        parts += [
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;",
            f"REVOKE ALL ON {table} FROM anon, authenticated;",
            f"GRANT SELECT ON {table} TO anon, authenticated;",
            f"CREATE POLICY public_read ON {table} FOR SELECT TO anon, authenticated USING (true);",
        ]
    user_tables = [t for t in Base.metadata.tables if t != "system_usage_daily"]
    for table in user_tables:
        owner = "id" if table == "profiles" else "user_id"
        parts += [
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;",
            f"REVOKE ALL ON {table} FROM anon, authenticated;",
            f"GRANT SELECT ON {table} TO authenticated;",
            f"CREATE POLICY own_rows ON {table} FOR SELECT TO authenticated USING ({owner} = (select auth.uid())::text);",
        ]
    parts += [
        "ALTER TABLE system_usage_daily ENABLE ROW LEVEL SECURITY;",
        "REVOKE ALL ON system_usage_daily FROM anon, authenticated;",
        "CREATE INDEX attempts_user_date ON submission_attempts(user_id,submitted_at DESC);",
        "CREATE INDEX jobs_claim ON execution_jobs(status,created_at);",
        "CREATE INDEX session_resume ON study_sessions(user_id,updated_at DESC);",
        "COMMIT;",
    ]
    path = ROOT / "supabase/migrations/202611030001_initial.sql"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(parts), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    generate()
