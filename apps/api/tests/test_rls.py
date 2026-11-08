import os
import uuid
from pathlib import Path
import pytest


def test_migration_locks_verified_state_and_secrets():
    migration = (Path(__file__).resolve().parents[3] / "supabase/migrations/202611030001_initial.sql").read_text(
        encoding="utf-8"
    )
    for table in (
        "submission_attempts",
        "user_concept_progress",
        "review_schedules",
        "problem_drafts",
        "execution_jobs",
    ):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in migration
        assert f"GRANT SELECT ON {table} TO authenticated" in migration
        assert f"GRANT UPDATE ON {table}" not in migration
    assert "REVOKE ALL ON ALL TABLES IN SCHEMA private FROM PUBLIC, anon, authenticated" in migration


@pytest.mark.skipif(
    not os.getenv("RLS_TEST_DATABASE_URL"), reason="Dedicated migrated Supabase test database not configured"
)
def test_live_rls_select_and_write_denial():
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError

    engine = create_engine(os.environ["RLS_TEST_DATABASE_URL"])
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    with engine.connect() as conn:
        tx = conn.begin()
        try:
            conn.execute(
                text("INSERT INTO profiles(id,display_name,created_at) VALUES (:a,'rls-a',now()),(:b,'rls-b',now())"),
                {"a": a, "b": b},
            )
            conn.execute(text("SET LOCAL ROLE authenticated"))
            conn.execute(text("SELECT set_config('request.jwt.claim.sub',:a,true)"), {"a": a})
            visible = (
                conn.execute(text("SELECT id FROM profiles WHERE id IN (:a,:b)"), {"a": a, "b": b}).scalars().all()
            )
            assert visible == [a]
            with pytest.raises(DBAPIError):
                with conn.begin_nested():
                    conn.execute(text("UPDATE user_concept_progress SET mastery_level=5 WHERE user_id=:a"), {"a": a})
        finally:
            tx.rollback()
    engine.dispose()
