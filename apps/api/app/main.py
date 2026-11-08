import hashlib
import time
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from . import schemas as s
from .auth import DEFAULT_SETTINGS, create_local_guest, current_user
from .config import ROOT, settings
from .content import CONCEPTS, DATA, VARIANTS, VERSIONS, problem, public_activity, public_problem, reading_projects
from .db import (
    ActivityProgress,
    Attempt,
    ConceptProgress,
    Draft,
    Job,
    Profile,
    Review,
    SessionItem,
    SessionFlow,
    StudySession,
    Usage,
    UserSettings,
    db_session,
    init_db,
    now,
    uid,
)
from .learning import aware, choose_queue, continuation_queue, update_learning
from content.activities import DEEP_DIVES


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="ML Code Trainer API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)
PREFIX = "/api/v1"


@app.middleware("http")
async def boundaries(request, call_next):
    rid = request.headers.get("X-Request-ID", "")
    request.state.request_id = rid if len(rid) < 100 and rid.isascii() and rid else uid()
    origin = request.headers.get("origin")
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin and origin != settings.web_origin:
        return JSONResponse(
            {
                "error": {
                    "code": "origin_rejected",
                    "message": "Origin not allowed",
                    "request_id": request.state.request_id,
                }
            },
            403,
        )
    if int(request.headers.get("content-length", "0") or 0) > 100000:
        return JSONResponse(
            {
                "error": {
                    "code": "payload_too_large",
                    "message": "Request too large",
                    "request_id": request.state.request_id,
                }
            },
            413,
        )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse(
        {"error": {"code": str(exc.status_code), "message": str(exc.detail), "request_id": request.state.request_id}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        {
            "error": {
                "code": "validation_error",
                "message": "入力値を確認してください。",
                "request_id": request.state.request_id,
            }
        },
        status_code=422,
    )


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    return JSONResponse(
        {
            "error": {
                "code": "system_error",
                "message": "サーバー処理に失敗しました。コードを保持して再試行してください。",
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
        status_code=500,
    )


def owned(db, model, id, user):
    row = db.get(model, id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Not found")
    return row


def serialize(row, exclude=()):
    return {
        c.name: (aware(getattr(row, c.name)) if isinstance(getattr(row, c.name), datetime) else getattr(row, c.name))
        for c in row.__table__.columns
        if c.name not in exclude
    }


def rate_limit(db, key, limit):
    bucket = f"{key}:{int(time.time() // 60)}"
    row = db.get(Usage, bucket)
    if not row:
        try:
            with db.begin_nested():
                db.add(Usage(key=bucket, count=0))
                db.flush()
        except IntegrityError:
            pass
    count = db.execute(
        update(Usage).where(Usage.key == bucket).values(count=Usage.count + 1).returning(Usage.count)
    ).scalar_one()
    db.commit()
    if count > limit:
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "60"})


def job_view(job):
    return {"id": job.id, "status": job.status, "code_hash": job.code_hash, "result": job.result}


@app.get(PREFIX + "/health")
def health():
    return {
        "ok": True,
        "mode": "supabase" if settings.supabase_url else "local",
        "sandbox": settings.modal_ready,
        "curriculum_version": DATA["version"],
    }


@app.post(PREFIX + "/auth/guest")
def guest(request: Request, response: Response, db: Session = Depends(db_session)):
    if settings.supabase_url:
        raise HTTPException(409, "Use Supabase anonymous sign-in")
    rate_limit(db, "guest-ip:" + (request.client.host if request.client else "local"), 20)
    from .auth import token_hash

    cookie = request.cookies.get("trainer_guest", "")
    user = db.query(Profile).filter_by(token_hash=token_hash(cookie)).first() if cookie else None
    if not user:
        user, token = create_local_guest(db)
        response.set_cookie(
            "trainer_guest",
            token,
            httponly=True,
            samesite="strict",
            secure=settings.app_env == "production",
            max_age=31536000,
            path="/api",
        )
    return {"id": user.id, "display_name": user.display_name, "mode": "local"}


@app.get(PREFIX + "/auth/me")
def me(user: Profile = Depends(current_user)):
    return {"id": user.id, "display_name": user.display_name, "mode": "supabase" if settings.supabase_url else "local"}


@app.get(PREFIX + "/modules")
def modules():
    return DATA["modules"]


@app.get(PREFIX + "/modules/{id}")
def module_detail(id: str):
    meta = next((m for m in DATA["modules"] if m["id"] == id), None)
    if not meta:
        raise HTTPException(404, "Module not found")
    return meta | {"concepts": [c for c in DATA["concepts"] if c["module_id"] == id]}


@app.get(PREFIX + "/concepts")
def concepts():
    return DATA["concepts"]


@app.get(PREFIX + "/concepts/{id}")
def concept_detail(id: str):
    if id not in CONCEPTS:
        raise HTTPException(404, "Concept not found")
    return CONCEPTS[id] | {"problems": [public_problem(p) for p in DATA["problems"] if p["concept_id"] == id]}


@app.get(PREFIX + "/problems/{id}", response_model=s.ProblemView)
def get_problem(id: str):
    p = problem(id)
    if not p:
        raise HTTPException(404, "Problem not found")
    return public_problem(p)


@app.get(PREFIX + "/runtime-harness", response_class=Response)
def runtime_harness():
    return Response((ROOT / "content/runner.py").read_text(encoding="utf-8"), media_type="text/plain")


def session_view(db, session):
    items = list(
        db.scalars(select(SessionItem).where(SessionItem.session_id == session.id).order_by(SessionItem.position))
    )
    flow = db.get(SessionFlow, session.id)
    return serialize(session) | {
        "items": [serialize(i) for i in items],
        "goal_count": flow.policy.get("count", 20) if flow else 20,
    }


@app.post(PREFIX + "/sessions", response_model=s.SessionView)
def create_session(body: s.SessionCreate, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    rate_limit(db, "sessions:" + user.id, 10)
    queue = choose_queue(db, user.id, body)
    if not queue:
        raise HTTPException(409, "この条件の問題はありません。復習予定やフィルターを確認してください。")
    session = StudySession(user_id=user.id, kind=body.kind)
    db.add(session)
    db.flush()
    policy = body.model_dump()
    if body.kind == "daily" and "count" not in body.model_fields_set:
        stored = db.get(UserSettings, user.id)
        policy["count"] = (stored.data if stored else {}).get("daily_goal", 20)
    db.add(SessionFlow(session_id=session.id, policy=policy, advances={}))
    for pos, p in enumerate(queue):
        last = (
            db.query(Attempt)
            .filter_by(user_id=user.id, problem_version_id=p["version_id"])
            .order_by(Attempt.submitted_at.desc())
            .first()
        )
        seed = 99 if last and last.variant_seed == 42 and 99 in VARIANTS else 42
        db.add(
            SessionItem(
                user_id=user.id,
                session_id=session.id,
                problem_version_id=p["version_id"],
                variant_seed=seed,
                position=pos,
            )
        )
    db.commit()
    return session_view(db, session)


@app.get(PREFIX + "/sessions/current", response_model=s.SessionView | None)
def current_session(user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    row = (
        db.query(StudySession)
        .filter(StudySession.user_id == user.id, StudySession.status != "completed")
        .order_by(StudySession.updated_at.desc())
        .first()
    )
    return session_view(db, row) if row else None


@app.get(PREFIX + "/sessions/{id}", response_model=s.SessionView)
def get_session(id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    return session_view(db, owned(db, StudySession, id, user))


@app.get(PREFIX + "/sessions/{id}/items/{item_id}", response_model=s.ItemDetailView)
def get_item(id: str, item_id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    item = owned(db, SessionItem, item_id, user)
    if item.session_id != id:
        raise HTTPException(404, "Item not found")
    return serialize(item) | {"problem": public_problem(problem(item.problem_version_id, item.variant_seed))}


@app.post(PREFIX + "/sessions/{id}/advance", response_model=s.AdvanceView)
def advance_session(
    id: str, body: s.AdvanceRequest, user: Profile = Depends(current_user), db: Session = Depends(db_session)
):
    row = owned(db, StudySession, id, user)
    previous = owned(db, SessionItem, body.from_item_id, user)
    if previous.session_id != id:
        raise HTTPException(404, "Item not found")
    # Same lock order as progress updates. The link from an item is persistent and
    # idempotent, including when a network response is lost or two tabs advance.
    db.execute(select(Profile).where(Profile.id == user.id).with_for_update())
    db.refresh(row)
    flow = db.get(SessionFlow, id)
    items = list(db.scalars(select(SessionItem).where(SessionItem.session_id == id).order_by(SessionItem.position)))
    if not flow:
        first = problem(items[0].problem_version_id, items[0].variant_seed)
        policy = {
            "kind": row.kind,
            "count": 20,
            "concept_id": first["concept_id"] if row.kind == "concept" else None,
            "modules": [],
            "stages": [],
        }
        if row.kind == "custom":
            cids = {problem(i.problem_version_id)["concept_id"] for i in items}
            if len(cids) == 1:
                # Old concept-stage buttons created custom sessions; recover their
                # progressive intent without renaming or deleting the old session.
                policy["legacy_progressive"] = True
                policy["concept_id"] = first["concept_id"]
            else:
                policy["modules"] = sorted({problem(i.problem_version_id)["module_id"] for i in items})
                policy["stages"] = sorted({problem(i.problem_version_id)["stage"] for i in items})
        flow = SessionFlow(session_id=id, policy=policy, advances={})
        db.add(flow)
    saved = (flow.advances or {}).get(previous.id)
    if saved:
        return {"session": session_view(db, row), "next_item_id": saved["item"], "message": saved["message"]}
    if row.status == "completed":
        raise HTTPException(409, "終了したセッションです。新しい演習を開始してください。")
    if not previous.completed and not body.skip:
        raise HTTPException(409, "答え合わせをするか、「この問題は後で」を選んでください。")
    next_item = next((i for i in items if i.position == previous.position + 1), None)
    message = ""
    if not next_item:
        queue, message = continuation_queue(db, user.id, row, flow.policy, previous, items)
        if not queue:
            return {"session": session_view(db, row), "next_item_id": None, "reason": message}
        for offset, p in enumerate(queue):
            recent = next((i for i in reversed(items) if i.problem_version_id.split("@")[0] == p["id"]), None)
            last = (
                db.query(Attempt)
                .filter_by(user_id=user.id, problem_version_id=p["version_id"])
                .order_by(Attempt.submitted_at.desc())
                .first()
            )
            last_seed = recent.variant_seed if recent else last.variant_seed if last else 99
            new = SessionItem(
                user_id=user.id,
                session_id=id,
                problem_version_id=p["version_id"],
                variant_seed=99 if last_seed == 42 and 99 in VARIANTS else 42,
                position=len(items) + offset,
            )
            db.add(new)
            if next_item is None:
                next_item = new
        db.flush()
    row.position, row.status, row.updated_at = next_item.position, "active", now()
    flow.advances = {**(flow.advances or {}), previous.id: {"item": next_item.id, "message": message}}
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        flow = db.get(SessionFlow, id)
        saved = (flow.advances or {}).get(previous.id) if flow else None
        if not saved:
            raise HTTPException(409, "次の問題の取得が重なりました。もう一度お試しください。")
        return {
            "session": session_view(db, db.get(StudySession, id)),
            "next_item_id": saved["item"],
            "message": saved["message"],
        }
    return {"session": session_view(db, row), "next_item_id": next_item.id, "message": message}


@app.post(PREFIX + "/sessions/{id}/{action}", response_model=s.SessionView)
def session_action(
    id: str,
    action: str,
    position: int | None = None,
    user: Profile = Depends(current_user),
    db: Session = Depends(db_session),
):
    row = owned(db, StudySession, id, user)
    if action not in ("pause", "resume", "complete"):
        raise HTTPException(404, "Unknown session action")
    row.status = {"pause": "paused", "resume": "active", "complete": "completed"}[action]
    if position is not None:
        count = db.query(SessionItem).filter_by(session_id=id).count()
        if not 0 <= position < count:
            raise HTTPException(422, "Invalid position")
        row.position = position
    row.updated_at = now()
    db.commit()
    return session_view(db, row)


@app.post(PREFIX + "/session-items/{id}/hints/{level}/reveal")
def hint(id: str, level: int, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    item = owned(db, SessionItem, id, user)
    if not 1 <= level <= 3:
        raise HTTPException(422, "Hint level must be 1–3")
    hints = problem(item.problem_version_id, item.variant_seed)["hints"]
    item.hint_level = max(item.hint_level, min(level, len(hints)))
    db.commit()
    return {"level": item.hint_level, "hints": hints[: item.hint_level]}


@app.get(PREFIX + "/session-items/{id}/last-submission", response_model=s.SubmissionView | None)
def last_submission(id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    owned(db, SessionItem, id, user)
    attempt = db.query(Attempt).filter_by(user_id=user.id, item_id=id).order_by(Attempt.submitted_at.desc()).first()
    return attempt_view(attempt) if attempt else None


@app.post(PREFIX + "/session-items/{id}/solution/reveal")
def solution(id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    item = owned(db, SessionItem, id, user)
    item.solution_viewed = True
    db.commit()
    p = problem(item.problem_version_id)
    return {"solution": p["solution"], "explanation": p["explanation"], "common_mistakes": p["common_mistakes"]}


@app.get(PREFIX + "/drafts/{item_id}", response_model=s.DraftView)
def get_draft(item_id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    owned(db, SessionItem, item_id, user)
    row = db.get(Draft, (user.id, item_id))
    return serialize(row) if row else {"code": None, "revision": 0}


@app.put(PREFIX + "/drafts/{item_id}", response_model=s.DraftView)
def put_draft(item_id: str, body: s.DraftPut, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    owned(db, SessionItem, item_id, user)
    row = db.get(Draft, (user.id, item_id))
    if not row:
        if body.revision != 0:
            raise HTTPException(409, "Draft revision conflict")
        row = Draft(user_id=user.id, item_id=item_id, code=body.code, revision=1)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Draft revision conflict")
    else:
        changed = db.execute(
            update(Draft)
            .where(Draft.user_id == user.id, Draft.item_id == item_id, Draft.revision == body.revision)
            .values(code=body.code, revision=body.revision + 1, updated_at=now())
        ).rowcount
        if changed != 1:
            db.rollback()
            raise HTTPException(409, "別のタブで更新されました。ローカル下書きを保持しています。")
        db.commit()
        db.refresh(row)
    return serialize(row)


def hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()


@app.post(PREFIX + "/executions", response_model=s.ExecutionView)
def create_execution(
    body: s.ExecutionRequest, request: Request, user: Profile = Depends(current_user), db: Session = Depends(db_session)
):
    item = owned(db, SessionItem, body.item_id, user)
    existing = db.query(Job).filter_by(user_id=user.id, request_id=body.client_request_id).first()
    if existing:
        if existing.code_hash != hash_code(body.code) or existing.item_id != item.id or existing.mode != body.mode:
            raise HTTPException(409, "Request ID already used with different content")
        return job_view(existing)
    if not settings.modal_ready:
        raise HTTPException(503, "実行環境が未設定です。docs/DEPLOYMENT.mdのModal設定を確認してください。")
    rate_limit(db, "execution-user:" + user.id, 10)
    rate_limit(db, "execution-ip:" + (request.client.host if request.client else ""), 30)
    job = Job(
        user_id=user.id,
        item_id=item.id,
        problem_version_id=item.problem_version_id,
        code=body.code,
        code_hash=hash_code(body.code),
        mode=body.mode,
        request_id=body.client_request_id,
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "同時実行は1件までです。実行完了またはキャンセルを待ってください。")
    return job_view(job)


@app.get(PREFIX + "/executions/{id}", response_model=s.ExecutionView)
def get_execution(id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    job = owned(db, Job, id, user)
    if (job.status == "running" and job.lease_until and aware(job.lease_until) < now()) or (
        job.status == "queued" and aware(job.created_at) < now() - timedelta(minutes=5)
    ):
        db.execute(
            update(Job)
            .where(Job.id == id, Job.status.in_(["queued", "running"]))
            .values(
                status="failed",
                finished_at=now(),
                result={
                    "verdict": "System Error",
                    "passed_tests": 0,
                    "total_tests": 0,
                    "stderr": "実行Workerの待機・応答期限を超えました。設定と稼働状態を確認してください。",
                },
            )
        )
        db.commit()
        db.refresh(job)
    return job_view(job)


@app.post(PREFIX + "/executions/{id}/cancel", response_model=s.ExecutionView)
def cancel_execution(id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    job = owned(db, Job, id, user)
    if job.status in ("queued", "running"):
        job.status = "cancelled"
        job.finished_at = now()
        db.commit()
    return job_view(job)


def attempt_view(a):
    return serialize(a)


@app.post(PREFIX + "/submissions", response_model=s.SubmissionView)
def submit(body: s.SubmissionRequest, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    old = db.query(Attempt).filter_by(user_id=user.id, client_request_id=body.client_request_id).first()
    if old:
        if old.item_id != body.item_id or old.code_hash != hash_code(body.code):
            raise HTTPException(409, "Request ID already used with different content")
        return attempt_view(old)
    rate_limit(db, "submission:" + user.id, 30)
    item = owned(db, SessionItem, body.item_id, user)
    p = problem(item.problem_version_id, item.variant_seed)
    verification = "browser_provisional"
    if body.execution_id:
        job = owned(db, Job, body.execution_id, user)
        if job.item_id != item.id or job.code_hash != hash_code(body.code) or job.mode != "submit":
            raise HTTPException(409, "Execution does not match this submission")
        if job.status != "completed" or not job.result:
            raise HTTPException(409, "Execution is not completed")
        result = job.result
        verification = "server_verified"
    elif body.browser_result and p["runtime"] == "browser":
        result = body.browser_result.model_dump(exclude={"tests"})
        if body.browser_result.tests is not None:
            # Browser runs know public cases only. Expectations come from the
            # trusted version, never from the submitted display information.
            result["tests"] = [
                observed.model_dump(exclude_unset=True)
                | {key: case[key] for key in ("expected", "expected_tuple_paths") if key in case}
                for observed, case in zip(body.browser_result.tests, p["public_tests"])
            ]
    else:
        raise HTTPException(503, "サーバー実行環境が必要です。正式採点の設定を確認してください。")
    a = Attempt(
        user_id=user.id,
        problem_version_id=item.problem_version_id,
        session_id=item.session_id,
        item_id=item.id,
        variant_seed=item.variant_seed,
        submitted_code=body.code,
        verdict=result["verdict"],
        verification_level=verification,
        passed_tests=result["passed_tests"],
        total_tests=result["total_tests"],
        run_count=body.run_count,
        hint_level_used=item.hint_level,
        solution_viewed=item.solution_viewed,
        client_request_id=body.client_request_id,
        code_hash=hash_code(body.code),
        result=result,
    )
    try:
        db.add(a)
        db.flush()
        # Serialize updates per user in PostgreSQL. Unique request ID protects retries.
        db.execute(select(Profile).where(Profile.id == user.id).with_for_update())
        update_learning(db, user.id, item, a)
        db.commit()
    except IntegrityError:
        db.rollback()
        old = db.query(Attempt).filter_by(user_id=user.id, client_request_id=body.client_request_id).first()
        if old and old.code_hash == hash_code(body.code) and old.item_id == item.id:
            return attempt_view(old)
        raise HTTPException(409, "Submission conflict; query by request ID")
    return attempt_view(a)


@app.get(PREFIX + "/submissions/by-request/{request_id}", response_model=s.SubmissionView)
def submission_request(request_id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    a = db.query(Attempt).filter_by(user_id=user.id, client_request_id=request_id).first()
    if not a:
        raise HTTPException(404, "Submission not found")
    return attempt_view(a)


@app.get(PREFIX + "/submissions/{id}", response_model=s.SubmissionView)
def get_submission(id: str, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    return attempt_view(owned(db, Attempt, id, user))


@app.get(PREFIX + "/settings", response_model=s.SettingsView)
def get_settings(user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    return DEFAULT_SETTINGS | db.get(UserSettings, user.id).data | {"display_name": user.display_name}


@app.patch(PREFIX + "/settings", response_model=s.SettingsView)
def patch_settings(body: s.SettingsPatch, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    row = db.get(UserSettings, user.id)
    changes = body.model_dump(exclude_none=True)
    row.data = DEFAULT_SETTINGS | row.data | changes
    if "display_name" in changes:
        user.display_name = changes["display_name"]
    db.commit()
    return row.data


@app.get(PREFIX + "/history", response_model=s.HistoryView)
def history(limit: int = 30, offset: int = 0, user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    if not 1 <= limit <= 100 or offset < 0:
        raise HTTPException(422, "Invalid pagination")
    query = db.query(Attempt).filter_by(user_id=user.id)
    return {
        "total": query.count(),
        "items": [attempt_view(a) for a in query.order_by(Attempt.submitted_at.desc()).offset(offset).limit(limit)],
    }


@app.get(PREFIX + "/progress/concepts")
def progress(user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    return [serialize(p) for p in db.scalars(select(ConceptProgress).where(ConceptProgress.user_id == user.id))]


@app.get(PREFIX + "/reviews/due")
def reviews(user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    return [serialize(r) for r in db.scalars(select(Review).where(Review.user_id == user.id).order_by(Review.due_at))]


@app.get(PREFIX + "/dashboard")
@app.get(PREFIX + "/progress/summary")
def dashboard(user: Profile = Depends(current_user), db: Session = Depends(db_session)):
    config = get_settings(user, db)
    zone = ZoneInfo(config["timezone"])
    today = now().astimezone(zone).date()
    attempts = list(db.scalars(select(Attempt).where(Attempt.user_id == user.id)))
    dates = Counter(aware(a.submitted_at).astimezone(zone).date() for a in attempts)
    streak = 0
    day = today if today in dates else today - timedelta(days=1)
    while day in dates:
        streak += 1
        day -= timedelta(days=1)
    ps = progress(user, db)
    rs = reviews(user, db)
    activities = [serialize(a) for a in db.scalars(select(ActivityProgress).where(ActivityProgress.user_id == user.id))]
    weekly = [
        {"date": str(today - timedelta(days=i)), "count": dates.get(today - timedelta(days=i), 0)}
        for i in reversed(range(7))
    ]
    abilities = {}
    for typ in ("completion", "prediction", "implementation", "bugfix"):
        records = [a for a in attempts if VERSIONS[a.problem_version_id]["type"] == typ]
        abilities[typ] = {"attempts": len(records), "accepted": sum(a.verdict == "Accepted" for a in records)}
    return {
        "user": {"id": user.id, "display_name": user.display_name},
        "settings": config,
        "total_attempts": len(attempts),
        "accepted": sum(a.verdict == "Accepted" for a in attempts),
        "today_count": dates.get(today, 0),
        "streak": streak,
        "study_days": len(dates),
        "weekly": weekly,
        "concepts": ps,
        "reviews": rs,
        "abilities": abilities,
        "activities": activities,
        "due_count": sum(aware(r["due_at"]) <= now() for r in rs),
        "mastered": sum(p["mastery_level"] >= 3 for p in ps),
        "current_session": current_session(user, db),
        "sandbox_available": settings.modal_ready,
        "auth_mode": "supabase" if settings.supabase_url else "local",
    }


@app.get(PREFIX + "/deep-dives")
def deep_dives():
    return [public_activity(t) for t in DEEP_DIVES]


@app.get(PREFIX + "/deep-dives/{id}")
def deep_dive(id: str):
    task = next((t for t in DEEP_DIVES if t["id"] == id), None)
    if not task:
        raise HTTPException(404, "Task not found")
    return public_activity(task)


@app.get(PREFIX + "/reading-projects")
def reading_list():
    return [public_activity(p) for p in reading_projects()]


@app.get(PREFIX + "/reading-projects/{id}")
def reading_detail(id: str):
    p = next((p for p in reading_projects() if p["id"] == id), None)
    if not p:
        raise HTTPException(404, "Project not found")
    return public_activity(p)


@app.post(PREFIX + "/activities/{id}/answers")
def answer_activity(
    id: str, body: s.ActivityAnswer, user: Profile = Depends(current_user), db: Session = Depends(db_session)
):
    activity = next((a for a in DEEP_DIVES + reading_projects() if a["id"] == id), None)
    q = next((q for q in activity["questions"] if q["id"] == body.question_id), None) if activity else None
    if not q or body.answer >= len(q["choices"]):
        raise HTTPException(422, "Unknown question or answer")
    ok = body.answer == q["answer"]
    row = db.get(ActivityProgress, (user.id, id, q["id"]))
    if row:
        row.accepted = row.accepted or ok
        row.answer = body.answer
        row.updated_at = now()
    else:
        db.add(ActivityProgress(user_id=user.id, activity_id=id, question_id=q["id"], accepted=ok, answer=body.answer))
    db.commit()
    return {"accepted": ok, "explanation": q["explanation"], "correct_answer": q["answer"]}
