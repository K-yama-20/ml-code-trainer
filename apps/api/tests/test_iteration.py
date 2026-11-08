from uuid import uuid4

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem
from apps.api.app.grading import judge
from content.iteration import LESSONS
from content.runner import run_payload

ORDER = [1, 7, 8, 2, 9, 10, 3, 11, 12, 4, 13, 14, 5, 15, 16, 6, 17, 18]
IDS = [f"PY01-{i:02}" for i in ORDER]


def test_iteration_matches_authored_copy_and_keeps_previous_versions():
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "PY01"]
        assert [p["id"] for p in questions] == IDS
        for p, lesson in zip(questions, LESSONS, strict=True):
            assert p["title"] == lesson["title"]
            assert p["description"] == lesson["task"]
            assert p["hints"] == [lesson["hint"]]
            assert p["solution"] == lesson["solution"]
            assert p["public_tests"][0]["expected"] == lesson["expected"]
            assert p["workspace"]["provided_code"] + "\n" + p["starter_code"].rstrip() == lesson["starter"]
            assert p["editable_regions"] == [{"start": 9, "end": 9}]
            if lesson["number"] <= 6:
                old = ARCHIVED_VARIANTS[(f'{p["id"]}@{p["content_version"] - 1}', seed)]
                assert old["family_id"] == p["family_id"]
                assert old["stage"] == p["stage"]


@pytest.mark.parametrize(("pid", "code", "accepted"), [
    ("01", "result = list(map(lambda n: n * 2, numbers))", False),
    ("01", "_decoy = [1 for n in numbers]\nresult = list(map(lambda n: n * 2, numbers))", False),
    ("01", "result = [4, -2, 8]", False),
    ("01", "result = [n + n for n in numbers]", True),
    ("02", "result = [n for n in filter(lambda n: n > 0, numbers)]", False),
    ("02", "result = [n for n in numbers if 0 < n]", True),
    ("03", "result = [i for i in range(len(scores)) if scores[i] >= 0.5]", False),
    ("03", "pairs = enumerate(scores)\nresult = [i for i, score in pairs if 0.5 <= score]", True),
    ("04", "result = [features[i] * weights[i] for i in range(min(len(features), len(weights)))]", False),
    ("04", "result = [w * f for w, f in zip(weights, features)]", True),
    ("05", "result = dict(zip(class_names, range(len(class_names))))", False),
    ("15", "result = {names[i]: scores[i] for i in range(min(len(names), len(scores)))}", False),
    ("06", "result = [x for x in sum(batches, [])]", False),
    ("18", "result = [[lr, bs] for lr in learning_rates for bs in batch_sizes]", False),
    ("18", "result = [(rate, size) for rate in learning_rates for size in batch_sizes]", True),
])
def test_iteration_checks_the_requested_syntax_and_result(pid, code, accepted):
    p = problem(f"PY01-{pid}")
    cases = p["public_tests"] + p["hidden_tests"]
    out = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    result = judge(out["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (result["verdict"] == "Accepted") is accepted


def test_concept_session_order_and_single_hint(client):
    c = client.get("/api/v1/concepts/PY01").json()
    assert [p["id"] for p in c["problems"]] == IDS
    assert c["problem_count"] == 18
    assert not {"hints", "solution", "hidden_tests"} & c["problems"][0].keys()
    response = client.post("/api/v1/sessions", json={"kind": "concept", "concept_id": "PY01", "count": 18})
    assert response.status_code == 200, response.text
    session = response.json()
    assert [i["problem_version_id"].split("@")[0] for i in session["items"]] == IDS
    item = session["items"][0]
    hint = client.post(f"/api/v1/session-items/{item['id']}/hints/2/reveal").json()
    assert hint == {"level": 1, "hints": [LESSONS[0]["hint"]]}
    result = client.post("/api/v1/submissions", json={
        "item_id": item["id"], "client_request_id": str(uuid4()), "code": LESSONS[0]["solution"],
        "browser_result": {"verdict": "Accepted", "passed_tests": 2, "total_tests": 2},
    })
    assert result.status_code == 200, result.text
    assert result.json()["hint_level_used"] == 1
    assert client.get("/api/v1/history").json()["total"] == 1


def test_daily_keeps_order_even_when_questions_are_skipped(client):
    response = client.post("/api/v1/sessions", json={"kind": "daily", "count": 2})
    assert response.status_code == 200, response.text
    session = response.json()
    item = session["items"][0]
    for pid in IDS:
        assert item["problem_version_id"].split("@")[0] == pid
        if pid == IDS[-1]:
            break
        response = client.post(f"/api/v1/sessions/{session['id']}/advance",
                               json={"from_item_id": item["id"], "skip": True})
        assert response.status_code == 200, response.text
        result = response.json()
        session = result["session"]
        item = next(i for i in session["items"] if i["id"] == result["next_item_id"])
    assert client.get("/api/v1/progress/concepts").json() == []
