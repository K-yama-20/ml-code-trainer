import json
from uuid import uuid4

import pytest

from apps.api.app.content import problem, public_problem
from apps.api.app.grading import judge
from apps.api.app.schemas import ProblemView
from content.runner import pack_expected, run_browser_payload, run_payload
from conftest import create_session


@pytest.mark.parametrize(("expression", "value", "paths"), [
    ("[(0.1, 16), (0.1, 32)]", [[0.1, 16], [0.1, 32]], [[0], [1]]),
    ("[[0.1, 16], [0.1, 32]]", [[0.1, 16], [0.1, 32]], []),
    ("[]", [], []),
    ("()", [], [[]]),
    ("[7]", [7], []),
    ("(7,)", [7], [[]]),
    ("([1, 2], (3, 4))", [[1, 2], [3, 4]], [[], [1]]),
    ('{"kind": "tuple", "tuple_paths": [[0]], "value": [(7,)]}',
     {"kind": "tuple", "tuple_paths": [[0]], "value": [[7]]}, [["value", 0]]),
])
def test_shared_python_json_transport_preserves_tuple_paths(expression, value, paths):
    payload = {"code": f"result = {expression}", "cases": [{"setup": "", "args": ""}],
               "execution": {"mode": "script", "inputs": [], "globals": []}}
    browser = json.loads(run_browser_payload(json.dumps(payload), ""))["outputs"][0]
    server = json.loads(json.dumps(run_payload(payload)))["outputs"][0]
    for output in (browser, server):
        assert output["value"] == value
        assert output["tuple_paths"] == paths


def test_expected_types_are_compiled_and_distributed_without_changing_grading():
    p = problem("PY01-18")
    exposed = ProblemView.model_validate(public_problem(p)).model_dump()
    assert exposed["public_tests"][0]["expected_tuple_paths"] == [[0], [1], [2], [3]]
    assert "hidden_tests" not in exposed and "solution" not in exposed
    assert problem("PY02-06")["public_tests"][0]["expected_tuple_paths"] == [[]]
    assert problem("NP01-02")["public_tests"][0]["expected_tuple_paths"] == [[]]
    public = {"setup": "", "args": "", **pack_expected([(7,)])}
    hidden = {"setup": "", "args": "", **pack_expected(("private",))}
    outputs = [{"value": [[7]], "tuple_paths": []}, {"value": ["private"], "tuple_paths": [[]]}]
    result = judge(outputs, [public, hidden], "pass", public_count=1)
    assert result["verdict"] == "Accepted"  # Display paths do not affect comparison.
    assert result["tests"][0]["actual_tuple_paths"] == []
    assert result["tests"][0]["expected_tuple_paths"] == [[0]]
    assert not {"actual", "expected", "actual_tuple_paths", "expected_tuple_paths"} & result["tests"][1].keys()


def test_browser_actual_types_survive_submission_and_history(client):
    session = create_session(client, "PY01", count=18)
    item = next(i for i in session["items"] if i["problem_version_id"].startswith("PY01-18@"))
    response = client.post("/api/v1/submissions", json={
        "item_id": item["id"], "code": "result = [(0.1, 16)]",
        "client_request_id": str(uuid4()),
        "browser_result": {
            "verdict": "Wrong Answer", "passed_tests": 0, "total_tests": 2,
            "tests": [{"name": "Test 1", "passed": False,
                       "actual": [[0.1, 16]], "actual_tuple_paths": [[0]]}],
        },
    })
    assert response.status_code == 200, response.text
    saved = response.json()
    reloaded = client.get(f"/api/v1/submissions/{saved['id']}").json()
    assert reloaded["result"] == saved["result"]
    first = reloaded["result"]["tests"][0]
    assert first["actual"] == [[0.1, 16]] and first["actual_tuple_paths"] == [[0]]
    assert first["expected_tuple_paths"] == [[0], [1], [2], [3]]
    assert first["expected"] != first["actual"]
    assert client.get(f"/api/v1/session-items/{item['id']}/last-submission").json()["result"] == saved["result"]
