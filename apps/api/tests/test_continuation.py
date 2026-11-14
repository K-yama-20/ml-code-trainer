import uuid
from fastapi.testclient import TestClient
from apps.api.app.db import Job, SessionFlow
from apps.api.app.main import app, hash_code
from apps.api.app.content import problem, DATA


# All 30 concepts are ordered 18-problem drills that keep their authored order.
# Certification still uses the stage gates (two families per stage, and a
# server-verified independent stage), which the tests below exercise on NP09.
STAGED = "NP09"
STAGES = ("guided", "partial", "independent")


def walk(client, session, database=None, verified_independent=False, hints=False):
    """Submit every queued item in order; return the concept/stage sequence."""
    seen = []
    current = session["items"][0]
    for _ in range(len(session["items"])):
        p = problem(current["problem_version_id"])
        seen.append((p["concept_id"], p["stage"]))
        if hints:
            client.post(f"/api/v1/session-items/{current['id']}/hints/1/reveal")
        verified = verified_independent and p["stage"] == "independent"
        submit(client, current, verified=verified, database=database)
        r = advance(client, session, current)
        session = r["session"]
        current = next(i for i in session["items"] if i["id"] == r["next_item_id"])
    return seen, session, current


def start(client, **options):
    r = client.post("/api/v1/sessions", json={"kind": "concept", "concept_id": STAGED, **options})
    assert r.status_code == 200, r.text
    return r.json()


def submit(client, item, verified=False, database=None):
    code = "def solve(x):\n    return x\n"
    body = {"item_id": item["id"], "code": code, "client_request_id": str(uuid.uuid4())}
    result = {"verdict": "Accepted", "passed_tests": 2, "total_tests": 2}
    if verified:
        user = client.get("/api/v1/auth/me").json()["id"]
        with database() as db:
            job = Job(
                user_id=user,
                item_id=item["id"],
                problem_version_id=item["problem_version_id"],
                code=code,
                code_hash=hash_code(code),
                mode="submit",
                status="completed",
                request_id=str(uuid.uuid4()),
                result=result,
            )
            db.add(job)
            db.commit()
            body["execution_id"] = job.id
    else:
        body["browser_result"] = result
    r = client.post("/api/v1/submissions", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def advance(client, session, item, **options):
    r = client.post(f"/api/v1/sessions/{session['id']}/advance", json={"from_item_id": item["id"], **options})
    assert r.status_code == 200, r.text
    value = r.json()
    assert value["session"]["status"] == "active"
    return value


def test_guided_partial_independent_and_related_continue(client, database):
    session = start(client)
    ordered = [p for p in DATA["problems"] if p["concept_id"] == STAGED]
    assert [i["problem_version_id"] for i in session["items"]] == [p["version_id"] for p in ordered]
    seen, session, current = walk(client, session, database, verified_independent=True)
    assert seen == [(STAGED, p["stage"]) for p in ordered]
    assert problem(current["problem_version_id"])["concept_id"] != STAGED
    progress = client.get("/api/v1/progress/concepts").json()[0]
    assert progress["mastery_level"] == 3
    assert client.get("/api/v1/history").json()["total"] == 18
    assert client.get("/api/v1/sessions/current").json()["id"] == session["id"]


def test_provisional_independent_can_continue_without_false_certification(client):
    seen, session, current = walk(client, start(client))
    assert problem(current["problem_version_id"])["concept_id"] != STAGED
    assert client.get("/api/v1/progress/concepts").json()[0]["mastery_level"] == 2


def test_concept_stage_selection_is_starting_point_not_a_permanent_filter(client):
    session = start(client, stages=["guided"])
    assert {problem(i["problem_version_id"])["stage"] for i in session["items"]} == {"guided"}
    seen, session, current = walk(client, session)
    assert problem(current["problem_version_id"])["concept_id"] == STAGED
    assert problem(current["problem_version_id"])["stage"] == "partial"


def test_starting_partial_does_not_force_guided_or_claim_missing_certification(client):
    session = start(client, stages=["partial"])
    seen, session, current = walk(client, session)
    assert {stage for _, stage in seen} == {"partial"}
    assert problem(current["problem_version_id"])["stage"] == "independent"
    assert client.get("/api/v1/progress/concepts").json()[0]["mastery_level"] == 0


def test_explicit_custom_library_and_stage_scope_is_preserved(client):
    session = start(client, kind="custom", concept_id=None, modules=["numpy"], stages=["guided"], count=2)
    for item in session["items"]:
        submit(client, item)
    r = advance(client, session, session["items"][-1])
    for i in r["session"]["items"][-2:]:
        p = problem(i["problem_version_id"])
        assert p["stage"] == "guided" and p["module_id"] == "numpy"


def test_more_than_twenty_questions_goal_is_not_a_boundary(client):
    session = start(client, kind="daily", count=1, concept_id=None)
    assert session["goal_count"] == 1
    current = session["items"][0]
    ids = set()
    for _ in range(23):
        ids.add(current["id"])
        submit(client, current)
        r = advance(client, session, current)
        session = r["session"]
        current = next(i for i in session["items"] if i["id"] == r["next_item_id"])
    assert len(ids) == 23 and session["position"] == 23
    assert client.get("/api/v1/history").json()["total"] == 23
    assert session["goal_count"] == 1 and len(session["items"]) >= 24


def test_advance_retry_is_idempotent_and_explicit_skip_does_not_submit(client):
    session = start(client)
    last = session["items"][-1]
    no = client.post(f"/api/v1/sessions/{session['id']}/advance", json={"from_item_id": last["id"]})
    assert no.status_code == 409
    r = advance(client, session, last, skip=True)
    again = advance(client, session, last, skip=True)
    assert r["next_item_id"] == again["next_item_id"]
    assert len(r["session"]["items"]) == len(again["session"]["items"])
    assert client.get("/api/v1/history").json()["total"] == 0
    assert client.get("/api/v1/progress/concepts").json() == []


def test_hints_keep_gate_and_retry_uses_another_variant(client):
    seen, session, current = walk(client, start(client), hints=True)
    # Hinted answers count as practice but never certify a stage.
    assert client.get("/api/v1/progress/concepts").json()[0]["mastery_level"] == 0
    assert current["hint_level"] == 0
    # Retrying the drill serves the other seed, with hints reset.
    retry = start(client)
    assert [i["problem_version_id"] for i in retry["items"]] == [i["problem_version_id"] for i in session["items"][:18]]
    assert all(i["variant_seed"] == 99 and i["hint_level"] == 0 for i in retry["items"])


def test_unavailable_scope_explains_and_remains_active(client):
    session = start(client, kind="custom", concept_id="PT02")
    r = advance(client, session, session["items"][-1], skip=True)
    assert r["next_item_id"] is None and "実行できる問題がありません" in r["reason"]
    assert client.get("/api/v1/sessions/current").json()["status"] == "active"


def test_old_sessions_and_old_seed_are_preserved(client, database):
    session = start(client)
    with database() as db:
        db.delete(db.get(SessionFlow, session["id"]))
        db.commit()
    r = advance(client, session, session["items"][-1], skip=True)
    assert r["next_item_id"]
    a = problem("NP05-01@1", 42)
    b = problem("NP05-01@1", 99)
    assert a["content_version"] == b["content_version"] == 1
    assert a["public_tests"][0]["expected"] != b["public_tests"][0]["expected"]
    assert problem("NP05-01@2")["presentation"]


def test_legacy_concept_stage_session_continues_progressively(client, database):
    session = start(client, kind="custom", stages=["guided"])
    with database() as db:
        db.delete(db.get(SessionFlow, session["id"]))
        db.commit()
    for item in session["items"]:
        submit(client, item)
    r = advance(client, session, session["items"][-1])
    current = next(i for i in r["session"]["items"] if i["id"] == r["next_item_id"])
    assert problem(current["problem_version_id"])["stage"] == "partial"


def test_continuation_and_last_submission_are_owner_scoped(client):
    session = start(client)
    item = session["items"][0]
    attempt = submit(client, item)
    assert client.get(f"/api/v1/session-items/{item['id']}/last-submission").json()["id"] == attempt["id"]
    with TestClient(app) as other:
        other.post("/api/v1/auth/guest")
        assert (
            other.post(
                f"/api/v1/sessions/{session['id']}/advance", json={"from_item_id": item["id"], "skip": True}
            ).status_code
            == 404
        )
        assert other.get(f"/api/v1/session-items/{item['id']}/last-submission").status_code == 404


def test_phase1_archives_are_unchanged_and_references_still_pass():
    from content.runner import run_payload
    from apps.api.app.grading import judge
    from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS
    from content.drill_phase1 import LESSONS

    assert len(LESSONS) == 15 and len(DATA["problems"]) == 540
    for seed, data in VARIANTS.items():
        for current in data["problems"]:
            if current["content_version"] == 1:
                continue
            p = ARCHIVED_VARIANTS[(current["id"] + ("@2" if current["id"] in LESSONS else "@1"), seed)]
            old = ARCHIVED_VARIANTS[(p["id"] + "@1", seed)]
            if p["id"] not in LESSONS:
                assert p == old
                continue
            assert p["version_id"] == p["id"] + "@2"
            assert p["solution"] == old["solution"]
            cases = p["public_tests"] + p["hidden_tests"]
            actual = run_payload({"code": p["solution"], "cases": cases})
            assert (
                judge(
                    actual["outputs"], cases, p["solution"], p["required_ast"], p["check_dtype"], p["protect_inputs"]
                )["verdict"]
                == "Accepted"
            ), p["id"]


def test_ordered_drill_concept_session_keeps_authored_order(client):
    r = client.post("/api/v1/sessions", json={"kind": "concept", "concept_id": "NP05"})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    ordered = [p["id"] for p in DATA["problems"] if p["concept_id"] == "NP05"]
    assert len(ordered) == 18
    assert [i["problem_version_id"].split("@")[0] for i in items] == ordered
    # Ordered drills show a single hint; a level-2 request records that one hint.
    reveal = client.post(f"/api/v1/session-items/{items[0]['id']}/hints/2/reveal").json()
    assert reveal["level"] == len(problem(items[0]["problem_version_id"])["hints"]) == 1
