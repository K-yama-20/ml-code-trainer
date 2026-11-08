import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from apps.api.app.db import Attempt, ConceptProgress, Job, ProblemProgress, Review, now
from apps.api.app.main import app, hash_code
from apps.api.app.content import PROBLEMS
from conftest import create_session


def payload(item, **kwargs):
    return {
        "item_id": item["id"],
        "code": "def solve(x):\n    return x.mean(axis=1)\n",
        "client_request_id": str(uuid.uuid4()),
        "browser_result": {"verdict": "Accepted", "passed_tests": 2, "total_tests": 2},
        **kwargs,
    }


def test_guest_and_empty_real_dashboard(client):
    me = client.get("/api/v1/auth/me").json()
    assert client.post("/api/v1/auth/guest").json()["id"] == me["id"]
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["total_attempts"] == 0 and dashboard["concepts"] == [] and dashboard["streak"] == 0
    assert dashboard["auth_mode"] == "local" and not dashboard["sandbox_available"]


@pytest.mark.parametrize("module", ["python", "numpy", "pandas", "sklearn", "pytorch"])
def test_curriculum_count_and_no_private_data(client, module):
    c = client.get("/api/v1/modules/" + module).json()["concepts"]
    for concept in c:
        data = client.get("/api/v1/concepts/" + concept["id"]).json()
        assert len(data["problems"]) == concept.get("problem_count", 6)
        for p in data["problems"]:
            assert "solution" not in p and "hidden_tests" not in p and "hints" not in p
            fixed = (p.get("presentation") or {}).get("answer",{}).get("mode") == "fixed"
            assert len(p["public_tests"]) == (1 if fixed else 2)


def test_session_pause_resume_and_draft_compare_and_swap(client):
    s = create_session(client)
    item = s["items"][0]
    path = f"/api/v1/drafts/{item['id']}"
    assert client.get(path).json()["revision"] == 0
    assert client.put(path, json={"code": "my code", "revision": 0}).json()["revision"] == 1
    conflict = client.put(path, json={"code": "lost code", "revision": 0})
    assert conflict.status_code == 409
    assert client.get(path).json()["code"] == "my code"
    assert client.post(f"/api/v1/sessions/{s['id']}/pause?position=1").json()["position"] == 1
    assert client.get("/api/v1/sessions/current").json()["status"] == "paused"
    assert client.post(f"/api/v1/sessions/{s['id']}/resume").json()["status"] == "active"
    assert client.post(f"/api/v1/sessions/{s['id']}/complete").status_code == 200
    assert client.get("/api/v1/sessions/current").json() is None


def test_idempotency_and_client_cannot_claim_verification(client, database):
    s = create_session(client)
    item = s["items"][0]
    body = payload(item)
    first = client.post("/api/v1/submissions", json=body)
    assert first.status_code == 200, first.text
    assert first.json()["verification_level"] == "browser_provisional"
    assert first.json()["submitted_at"].endswith(("+00:00", "Z"))
    second = client.post("/api/v1/submissions", json=body)
    assert second.json()["id"] == first.json()["id"]
    assert client.get("/api/v1/history").json()["total"] == 1
    with database() as db:
        assert db.query(ProblemProgress).one().data["attempts"] == 1
    assert client.get("/api/v1/submissions/by-request/" + body["client_request_id"]).json()["id"] == first.json()["id"]
    assert client.post("/api/v1/submissions", json={**body, "code": "different"}).status_code == 409
    assert client.post("/api/v1/submissions", json={**body, "verification_level": "server_verified"}).status_code == 422
    assert client.post("/api/v1/submissions", json={**body, "accepted": True}).status_code == 422


def test_hints_and_solution_prevent_clean_progress(client):
    s = create_session(client)
    item = s["items"][0]
    assert client.post(f"/api/v1/session-items/{item['id']}/hints/2/reveal").json()["level"] == 2
    assert client.post(f"/api/v1/session-items/{item['id']}/hints/1/reveal").json()["level"] == 2
    assert "solution" in client.post(f"/api/v1/session-items/{item['id']}/solution/reveal").json()
    a = client.post("/api/v1/submissions", json=payload(item)).json()
    assert a["hint_level_used"] == 2 and a["solution_viewed"]
    p = client.get("/api/v1/progress/concepts").json()[0]
    assert p["mastery_level"] == 0
    assert client.get("/api/v1/reviews/due").json()[0]["interval_days"] == 1


def test_stage_gates_distinct_families_and_formal_independent(client, database):
    s = create_session(client)
    user = client.get("/api/v1/auth/me").json()["id"]
    items = sorted(s["items"], key=lambda i: i["problem_version_id"])
    for item in items[:4]:
        body = payload(item)
        assert client.post("/api/v1/submissions", json=body).status_code == 200
        # Same family twice must not satisfy a two-family requirement.
        assert client.post("/api/v1/submissions", json=payload(item)).status_code == 200
    progress = client.get("/api/v1/progress/concepts").json()[0]
    assert progress["mastery_level"] == 2 and progress["current_stage"] == "independent"
    for item in items[4:]:
        assert client.post("/api/v1/submissions", json=payload(item)).status_code == 200
    assert client.get("/api/v1/progress/concepts").json()[0]["mastery_level"] == 2
    for item in items[4:]:
        body = payload(item)
        result = {"verdict": "Accepted", "passed_tests": 4, "total_tests": 4}
        with database() as db:
            job = Job(
                user_id=user,
                item_id=item["id"],
                problem_version_id=item["problem_version_id"],
                code=body["code"],
                code_hash=hash_code(body["code"]),
                mode="submit",
                status="completed",
                request_id=str(uuid.uuid4()),
                result=result,
            )
            db.add(job)
            db.commit()
            id = job.id
        body.pop("browser_result")
        assert (
            client.post("/api/v1/submissions", json={**body, "execution_id": id}).json()["verification_level"]
            == "server_verified"
        )
    assert client.get("/api/v1/progress/concepts").json()[0]["mastery_level"] == 3


def test_wrong_answer_preserves_draft_and_shortens_review(client, database):
    s = create_session(client)
    item = s["items"][0]
    client.put("/api/v1/drafts/" + item["id"], json={"code": "my wrong code", "revision": 0})
    body = payload(item, browser_result={"verdict": "Wrong Answer", "passed_tests": 0, "total_tests": 2})
    assert client.post("/api/v1/submissions", json=body).status_code == 200
    assert client.get("/api/v1/drafts/" + item["id"]).json()["code"] == "my wrong code"
    user = client.get("/api/v1/auth/me").json()["id"]
    with database() as db:
        r = db.get(Review, (user, "NP05"))
        r.due_at = now() - timedelta(days=1)
        r.success_streak = 3
        r.interval_days = 14
        db.commit()
    client.post("/api/v1/submissions", json=payload(item, browser_result=body["browser_result"]))
    assert client.get("/api/v1/reviews/due").json()[0]["interval_days"] == 1


def test_provider_disabled_never_fakes_success(client):
    s = create_session(client, "PT04")
    body = payload(s["items"][0])
    body.pop("browser_result")
    assert client.post("/api/v1/executions", json=body).status_code == 503
    assert (
        client.post(
            "/api/v1/submissions",
            json={**body, "browser_result": {"verdict": "Accepted", "passed_tests": 2, "total_tests": 2}},
        ).status_code
        == 503
    )
    assert client.get("/api/v1/history").json()["total"] == 0


def test_cross_user_access_is_404(client, database):
    session = create_session(client)
    item = session["items"][0]
    a = client.post("/api/v1/submissions", json=payload(item)).json()
    with TestClient(app) as other:
        other.post("/api/v1/auth/guest")
        assert other.get("/api/v1/history").json()["total"] == 0
        for url in [f"/sessions/{session['id']}", f"/drafts/{item['id']}", f"/submissions/{a['id']}"]:
            assert other.get("/api/v1" + url).status_code == 404
        assert other.put("/api/v1/drafts/" + item["id"], json={"code": "overwrite", "revision": 0}).status_code == 404
        assert other.post("/api/v1/submissions", json=payload(item)).status_code == 404
        assert other.post(f"/api/v1/session-items/{item['id']}/solution/reveal").status_code == 404


def test_executions_bound_to_code_item_and_submit_mode(client, database):
    s = create_session(client)
    item = s["items"][0]
    body = payload(item)
    user = client.get("/api/v1/auth/me").json()["id"]
    with database() as db:
        j = Job(
            user_id=user,
            item_id=item["id"],
            problem_version_id=item["problem_version_id"],
            code="other",
            code_hash=hash_code("other"),
            mode="run",
            status="completed",
            request_id=str(uuid.uuid4()),
            result={"verdict": "Accepted", "passed_tests": 4, "total_tests": 4},
        )
        db.add(j)
        db.commit()
        id = j.id
    assert client.post("/api/v1/submissions", json={**body, "execution_id": id}).status_code == 409


def test_settings_timezone_and_error_contract(client):
    assert (
        client.patch(
            "/api/v1/settings",
            json={"theme": "light", "font_size": 18, "daily_goal": 30, "timezone": "UTC", "display_name": "Test"},
        ).status_code
        == 200
    )
    assert client.get("/api/v1/settings").json()["daily_goal"] == 30
    assert client.patch("/api/v1/settings", json={"timezone": "nonsense"}).status_code == 422
    assert client.patch("/api/v1/settings", json={"daily_goal": 0}).status_code == 422
    assert client.post("/api/v1/sessions", json={}, headers={"Origin": "https://attacker.invalid"}).status_code == 403
    error = client.get("/api/v1/history?limit=1000").json()["error"]
    assert all(k in error for k in ("code", "message", "request_id"))


def test_transaction_rolls_back(client, database, monkeypatch):
    import apps.api.app.main as main

    s = create_session(client)

    def fail(*args):
        raise RuntimeError("Test transaction failure")

    monkeypatch.setattr(main, "update_learning", fail)
    with pytest.raises(RuntimeError):
        client.post("/api/v1/submissions", json=payload(s["items"][0]))
    with database() as db:
        assert db.query(Attempt).count() == 0 and db.query(ConceptProgress).count() == 0


def test_review_variants_change(client, database):
    s = create_session(client)
    for item in s["items"]:
        client.post("/api/v1/submissions", json=payload(item))
    other = create_session(client)
    assert all(i["variant_seed"] == 99 for i in other["items"])


def test_old_version_remains_in_history(client, database):
    from apps.api.app.db import SessionItem
    s = create_session(client)
    # Simulate an existing v1 session after publishing the new lesson.
    with database() as db:
        item = db.get(SessionItem,s["items"][0]["id"])
        item.problem_version_id = item.problem_version_id.split("@")[0]+"@1"
        db.commit()
    first = client.post("/api/v1/submissions", json=payload(s["items"][0])).json()
    assert "@1" in client.get("/api/v1/submissions/" + first["id"]).json()["problem_version_id"]
    assert first["problem_version_id"].split("@")[0] in PROBLEMS
    assert client.get("/api/v1/problems/" + first["problem_version_id"]).status_code == 200
    assert client.get("/api/v1/problems/" + first["problem_version_id"].split("@")[0] + "@999").status_code == 404


def test_code_size_is_limited_in_utf8_bytes(client):
    s = create_session(client)
    body = payload(s["items"][0], code="あ" * 6000)
    assert client.post("/api/v1/submissions", json=body).status_code == 422
