from datetime import timedelta

from apps.api.app.content import CONCEPTS, DATA, problem
from apps.api.app.db import Review, now
from test_api import payload


def start(client, **options):
    response = client.post("/api/v1/sessions", json=options)
    assert response.status_code == 200, response.text
    return response.json()


def test_sql_ordered_course_and_browser_only_progress(client):
    session = start(client, kind="concept", concept_id="SQL01")
    assert len(session["items"]) == session["goal_count"] == 3
    expected = [p["version_id"] for p in DATA["problems"] if p.get("sql")]
    assert len(expected) == 29
    item = session["items"][0]
    for version in expected:
        assert item["problem_version_id"] == version
        p = problem(version, item["variant_seed"])
        path = f"/api/v1/sessions/{session['id']}/items/{item['id']}"
        public = client.get(path).json()["problem"]
        assert public["sql"] == p["sql"]
        assert p["hidden_tests"][0] not in public["sql"]["cases"]
        body = payload(item, code=p["solution"])
        if version == expected[0]:
            job = {k: body[k] for k in ("code", "item_id", "client_request_id")}
            assert client.post("/api/v1/executions", json=job).status_code == 422
            assert client.post("/api/v1/submissions", json=body | {"execution_id": "test-id"}).status_code == 422
        submitted = client.post("/api/v1/submissions", json=body)
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["verification_level"] == "browser_provisional"
        response = client.post(f"/api/v1/sessions/{session['id']}/advance", json={"from_item_id": item["id"]})
        assert response.status_code == 200, response.text
        next_step = response.json()
        if next_step["next_item_id"]:
            item = next(i for i in next_step["session"]["items"] if i["id"] == next_step["next_item_id"])
    assert next_step["next_item_id"] is None and next_step["reason"]
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["mastered"] == 0
    assert dashboard["total_attempts"] == dashboard["accepted"] == 29
    assert dashboard["practice_completed"] == {
        c["id"]: c["problem_count"] for c in DATA["concepts"] if c["module_id"] == "sql"
    }
    assert all(p["mastery_level"] == 0 and p["last_verified_at"] is None for p in dashboard["concepts"])


def test_short_concept_review_and_retries(client, database, monkeypatch):
    # A concept with a single Independent problem can still be used from Daily
    # or Review by a learner whose formal current stage is Guided.
    pid = "SQL01-03"
    monkeypatch.setitem(DATA, "problems", [p for p in DATA["problems"] if p["concept_id"] != "SQL01" or p["id"] == pid])
    monkeypatch.setitem(CONCEPTS, "SQL01", CONCEPTS["SQL01"] | {"problem_count": 1})
    session = start(client, kind="daily", concept_id="SQL01", modules=["sql"])
    assert len(session["items"]) == 1
    item = session["items"][0]
    assert item["problem_version_id"] == f"{pid}@1"
    assert client.post("/api/v1/submissions", json=payload(item)).status_code == 200
    user = client.get("/api/v1/auth/me").json()["id"]
    with database() as db:
        db.get(Review, (user, "SQL01")).due_at = now() - timedelta(days=1)
        db.commit()
    review = start(client, kind="review", modules=["sql"])
    assert len(review["items"]) == 1
    assert review["items"][0]["problem_version_id"] == f"{pid}@1"
    assert review["items"][0]["variant_seed"] == 99
    assert client.post("/api/v1/submissions", json=payload(review["items"][0])).status_code == 200
    dashboard = client.get("/api/v1/dashboard").json()
    assert dashboard["practice_completed"] == {"SQL01": 1}
    assert dashboard["mastered"] == dashboard["due_count"] == 0
