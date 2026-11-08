"""Local SQLite and deployment PostgreSQL share the same durable domain schema."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(String, primary_key=True, default=uid)
    token_hash = Column(String, unique=True, nullable=True)
    display_name = Column(String, default="Learner", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)


class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    data = Column(JSON, nullable=False, default=dict)


class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(String, primary_key=True, default=uid)
    user_id = Column(String, ForeignKey("profiles.id"), index=True, nullable=False)
    kind = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)
    position = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, nullable=False)


class SessionItem(Base):
    __tablename__ = "session_items"
    id = Column(String, primary_key=True, default=uid)
    user_id = Column(String, ForeignKey("profiles.id"), index=True, nullable=False)
    session_id = Column(String, ForeignKey("study_sessions.id"), index=True, nullable=False)
    problem_version_id = Column(String, nullable=False)
    variant_seed = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    hint_level = Column(Integer, default=0, nullable=False)
    solution_viewed = Column(Boolean, default=False, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    __table_args__ = (UniqueConstraint("session_id", "position"),)


class SessionFlow(Base):
    """Additive continuation state. Existing session items and attempts stay immutable."""
    __tablename__ = "session_flows"
    session_id = Column(String, ForeignKey("study_sessions.id"), primary_key=True)
    policy = Column(JSON, nullable=False, default=dict)
    advances = Column(JSON, nullable=False, default=dict)


class Draft(Base):
    __tablename__ = "problem_drafts"
    user_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    item_id = Column(String, ForeignKey("session_items.id"), primary_key=True)
    code = Column(Text, nullable=False)
    revision = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Attempt(Base):
    __tablename__ = "submission_attempts"
    id = Column(String, primary_key=True, default=uid)
    user_id = Column(String, ForeignKey("profiles.id"), index=True, nullable=False)
    problem_version_id = Column(String, nullable=False)
    session_id = Column(String, ForeignKey("study_sessions.id"), nullable=False)
    item_id = Column(String, ForeignKey("session_items.id"), nullable=False)
    variant_seed = Column(Integer, nullable=False)
    submitted_code = Column(Text, nullable=False)
    verdict = Column(String, nullable=False)
    verification_level = Column(String, nullable=False)
    passed_tests = Column(Integer, default=0, nullable=False)
    total_tests = Column(Integer, default=0, nullable=False)
    run_count = Column(Integer, default=0, nullable=False)
    hint_level_used = Column(Integer, default=0, nullable=False)
    solution_viewed = Column(Boolean, default=False, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=now, nullable=False)
    client_request_id = Column(String, nullable=False)
    code_hash = Column(String, nullable=False)
    result = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "client_request_id"),)


class ConceptProgress(Base):
    __tablename__ = "user_concept_progress"
    user_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    concept_id = Column(String, primary_key=True)
    mastery_level = Column(Integer, default=0, nullable=False)
    mastery_score = Column(Float, default=0, nullable=False)
    current_stage = Column(String, default="guided", nullable=False)
    stage_families = Column(JSON, default=dict, nullable=False)
    last_practiced_at = Column(DateTime(timezone=True), default=now, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)


class ProblemProgress(Base):
    __tablename__ = "user_problem_progress"
    user_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    problem_version_id = Column(String, primary_key=True)
    data = Column(JSON, default=dict, nullable=False)


class Review(Base):
    __tablename__ = "review_schedules"
    user_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    concept_id = Column(String, primary_key=True)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    interval_days = Column(Integer, default=1, nullable=False)
    success_streak = Column(Integer, default=0, nullable=False)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    last_problem_family_id = Column(String, nullable=False)
    algorithm_version = Column(String, default="interval-v1", nullable=False)


class Job(Base):
    __tablename__ = "execution_jobs"
    id = Column(String, primary_key=True, default=uid)
    user_id = Column(String, ForeignKey("profiles.id"), index=True, nullable=False)
    item_id = Column(String, ForeignKey("session_items.id"), nullable=False)
    problem_version_id = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    code_hash = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    status = Column(String, default="queued", nullable=False)
    request_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)
    provider_id = Column(String, nullable=True)
    limits = Column(JSON, default=lambda: dict(timeout=30, memory=2048, cpu=1), nullable=False)
    result = Column(JSON, nullable=True)
    __table_args__ = (
        UniqueConstraint("user_id", "request_id"),
        Index(
            "one_active_job_per_user",
            "user_id",
            unique=True,
            sqlite_where=text("status IN ('queued','running')"),
            postgresql_where=text("status IN ('queued','running')"),
        ),
    )


class ActivityProgress(Base):
    __tablename__ = "activity_progress"
    user_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    activity_id = Column(String, primary_key=True)
    question_id = Column(String, primary_key=True)
    accepted = Column(Boolean, nullable=False)
    answer = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now, nullable=False)


class Usage(Base):
    __tablename__ = "system_usage_daily"
    key = Column(String, primary_key=True)
    count = Column(Integer, default=0, nullable=False)


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 20} if settings.database_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_options(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db():
    if settings.app_env != "production":
        Base.metadata.create_all(engine)


def db_session():
    with SessionLocal() as db:
        yield db
