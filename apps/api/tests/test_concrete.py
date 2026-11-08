import pytest

from apps.api.app.content import DATA, VARIANTS, problem, public_problem
from apps.api.app.grading import judge, equivalent, static_check
from content.runner import run_payload, pack
from content.concrete import PILOT


def evaluate(p, code=None):
    code = code or p["solution"]
    cases = p["public_tests"] + p["hidden_tests"]
    out = run_payload({"code": code, "cases": cases, "execution": p.get("execution", {})})
    return judge(
        out["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"], len(p["public_tests"])
    )


def test_all_versioned_workspaces_and_reference_solutions():
    assert len(PILOT) == 15
    for seed, data in VARIANTS.items():
        assert len(data["problems"]) == 288
        for p in data["problems"]:
            assert p["workspace"]["provided_code"] or (
                p["editable_regions"] and p["starter_code"] and p["workspace"]["invocation"]
            )
            assert evaluate(p)["verdict"] == "Accepted", (p["id"], seed)
            if p["content_version"] > 1:
                previous = problem(p["id"] + f"@{p['content_version'] - 1}", seed)
                assert previous and previous["version_id"] != p["version_id"]
            public = public_problem(p)
            assert not {"solution", "hidden_tests", "hints"}.intersection(public)
            if p["workspace"]["mode"] == "script":
                assert not p["solution"].startswith("def solve(")
                # A copied displayed answer is not a solution to the varied cases.
                from content.concrete import literal

                env = {}
                exec(p["workspace"]["provided_code"], env)
                exec(p["solution"], env)
                if p["workspace"].get("invocation"):
                    exec(p["workspace"]["invocation"], env)
                value = env["result"]
                if type(value).__module__.split(".")[0] == "torch":
                    value = value.contiguous()
                assert evaluate(p, "result = " + literal(value))["verdict"] != "Accepted", p["id"]


def test_displayed_program_matches_the_actual_public_input():
    for p in DATA["problems"]:
        env = {}
        exec(p["workspace"]["provided_code"], env)
        mode = p["workspace"]["mode"]
        if mode == "prediction":
            actual = pack(env["observed"])
        else:
            exec(p["solution"], env)
            if p["workspace"].get("invocation"):
                exec(p["workspace"]["invocation"], env)
            actual = pack(env["result"])
        assert equivalent(actual, p["public_tests"][0]["expected"], check_dtype=p["check_dtype"]), p["id"]


@pytest.mark.parametrize(
    "code",
    [
        "x = np.array([[1.,4.,5.],[2.,10.,-4.]])\nresult = x.mean(axis=1)",
        "x[:] = 0\nresult = x.mean(axis=1)",
        "globals()['x'] = np.array([[1.,4.,5.],[2.,10.,-4.]])\nresult=x.mean(axis=1)",
        "result = np.array([10/3,8/3])",
    ],
)
def test_input_replacement_mutation_and_hardcoded_answers_fail(code):
    assert evaluate(problem("NP05-01"), code)["verdict"] != "Accepted"


@pytest.mark.parametrize(
    "code",
    [
        "result = np.mean(x, axis=1)",
        "result = np.sum(x, axis=1) / x.shape[1]",
        "result = np.array([sum(row)/len(row) for row in x])",
        "x *= 2\nresult = x.mean(axis=1)/2",
    ],
)
def test_valid_alternative_algorithms_are_accepted(code):
    assert evaluate(problem("NP05-01"), code)["verdict"] == "Accepted"


def test_api_goal_requires_call_and_local_shadowing_is_legal():
    assert not static_check("method = model.eval\nresult = False", "call:eval")
    assert static_check("model.eval()\nresult=model.training", "call:eval")
    code = "def average(x):\n    x = x.copy()\n    return x.mean(axis=1)\nresult = average(x)"
    assert evaluate(problem("NP05-01"), code)["verdict"] == "Accepted"
    p = problem("PT05-04")
    counted = p["solution"].replace(
        "result = len(list(Model().parameters()))",
        "result = 0\nfor parameter in Model().parameters():\n    result += 1",
    )
    assert evaluate(p, counted)["verdict"] == "Accepted"


def test_client_cannot_override_execution_contract(client):
    session = client.post("/api/v1/sessions", json={"kind": "custom", "concept_id": "NP05", "count": 2}).json()
    item = session["items"][0]
    data = {
        "item_id": item["id"],
        "code": "result=1",
        "mode": "submit",
        "client_request_id": "contract",
        "execution": {"mode": "function"},
    }
    assert client.post("/api/v1/executions", json=data).status_code == 422


def test_print_without_result_explains_where_to_put_the_answer():
    result = evaluate(problem("NP05-01"), "print(x.mean(axis=1))")
    assert result["verdict"] == "Runtime Error"
    assert "resultに代入" in result["stderr"]


@pytest.mark.parametrize("cancel", [False, True])
def test_server_worker_isolates_private_inputs_and_preserves_cancellation(client, database, monkeypatch, cancel):
    from apps.api.app import worker
    from apps.api.app.db import Job, SessionItem
    from apps.api.app.main import hash_code

    session = client.post("/api/v1/sessions", json={"kind": "custom", "concept_id": "NP05", "count": 2}).json()
    source = "print(x)\nresult = x * 2\n"
    with database() as db:
        item = db.get(SessionItem, session["items"][0]["id"])
        job = Job(
            user_id=item.user_id,
            item_id=item.id,
            problem_version_id=item.problem_version_id,
            code=source,
            code_hash=hash_code(source),
            mode="submit",
            request_id="isolated",
            status="running",
        )
        db.add(job)
        db.commit()
        job_id = job.id
    p = {
        "public_tests": [{"setup": "", "args": "3", "expected": 6}],
        "hidden_tests": [{"setup": "", "args": "123456", "expected": 246912}],
        "execution": {"mode": "script", "inputs": ["x"], "globals": []},
        "required_ast": "",
        "check_dtype": False,
        "protect_inputs": True,
    }
    monkeypatch.setattr(worker, "SessionLocal", database)
    monkeypatch.setattr(worker, "problem", lambda *args: p)

    class Provider:
        def __init__(self):
            self.payloads = []
            self.cancelled = []

        def create_execution(self, payload, created):
            self.payloads.append(payload)
            sid = str(len(self.payloads))
            created(sid)
            return sid

        def get_execution_result(self, sid):
            if cancel and sid == "1":
                with database() as db:
                    db.get(Job, job_id).status = "cancelled"
                    db.commit()
            return run_payload(self.payloads[int(sid) - 1])

        def cancel_execution(self, sid):
            self.cancelled.append(sid)

    provider = Provider()
    worker.execute_job(provider, job_id)
    assert len(provider.payloads) == 2
    assert provider.payloads[0]["cases"] == [{"setup": "", "args": "3"}]
    assert "expected" not in provider.payloads[1]["cases"][0]
    with database() as db:
        job = db.get(Job, job_id)
        if cancel:
            assert job.status == "cancelled" and job.result is None
            assert provider.cancelled == ["2"]
        else:
            assert job.status == "completed" and job.result["verdict"] == "Accepted"
            assert job.result["stdout"].strip() == "3" and len(job.result["tests"]) == 1
