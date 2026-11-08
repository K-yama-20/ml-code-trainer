from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.reshaping import LESSONS
from content.runner import run_payload


def test_reshaping_order_authored_copy_constraints_and_old_versions():
    mapped = {1: 2, 2: 8, 3: 9, 4: 13, 5: 15, 6: 4}
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP03"]
        assert len(questions) == 18
        assert [p["id"] for p in questions] == [lesson["id"] for lesson in LESSONS]
        assert Counter(p["stage"] for p in questions) == dict.fromkeys(
            ("guided", "partial", "independent"), 6
        )
        for p, lesson in zip(questions, LESSONS, strict=True):
            assert p["title"] == lesson["title"] and p["description"] == lesson["task"]
            assert p["hints"] == [lesson["hint"]] and p["solution"] == lesson["solution"]
            assert p["workspace"]["provided_code"] == (
                "import numpy as np\n\n" + lesson["input"] + "\n\n# 以下に答えを記入"
            )
            assert p["starter_code"] == "result = "
            assert p["editable_regions"] == [{"start": 9, "end": 9}]
            assert not {"solution", "hidden_tests", "hints"} & public_problem(p).keys()
            for case in p["public_tests"] + p["hidden_tests"]:
                env = {}
                exec(case["setup"], env)
                x, number = env["x"], lesson["number"]
                assert case["expected"]["kind"] == "array"
                if number == 1:
                    assert x.size == env["rows"] * env["cols"]
                if number in (2, 3):
                    size = env["width"] if number == 2 else env["rows"]
                    assert size > 0 and x.size % size == 0
                if number == 7:
                    assert x.ndim == 0 and case["expected"]["shape"] == [1]
                if number in (8, 9, 10):
                    assert x.ndim == 2
                if number == 11:
                    assert x.ndim == 1 and case["expected"]["shape"] == [1, x.size, 1]
                if number == 13:
                    assert x.ndim == 3 and x.shape[0] == x.shape[-1] == 1
                if number == 14:
                    assert x.ndim == 3 and x.shape[-1] == 1
                    assert case["expected"]["shape"] == list(x.shape[:2])
                if number == 15:
                    assert x.ndim == 3 and x.shape[0] >= 1
                if number == 16:
                    assert x.ndim == 2 and x.shape[1] == env["height"] * env["width"]
                if number == 17:
                    assert x.ndim == 4 and x.shape[0] >= 1 and x.shape[-1] >= 1
                if number == 18:
                    assert x.ndim == 3 and x.shape[0] == 0
                    assert case["expected"]["shape"] == [0, x.shape[1] * x.shape[2]]
        assert any(case["expected"]["shape"] == []
                   for case in questions[11]["public_tests"] + questions[11]["hidden_tests"])
        for old_number, display_number in mapped.items():
            p = questions[display_number - 1]
            assert p["id"] == f"NP03-{old_number:02}"
            previous = f'{p["id"]}@{p["content_version"] - 1}'
            old = ARCHIVED_VARIANTS[(previous, seed)]
            assert problem(previous, seed) == old and old["stage"] == p["stage"]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = x.reshape(cols, rows).T", False),
    (1, "result = np.reshape(x, (rows, cols))", True),
    (2, "result = x.reshape(x.size // width, width)", False),
    (2, "infer = -1\nresult = np.reshape(x, (infer, width))", True),
    (3, "result = x.reshape(rows, x.size // rows)", False),
    (4, "result = x.reshape(-1, order='F')", False),
    (4, "result = x.ravel()", False),
    (5, "result = x.reshape(-1, 1)", False),
    (6, "result = x.reshape(1, -1)", False),
    (7, "result = x.reshape(())", False),
    (8, "result = np.expand_dims(x, 1)", False),
    (8, "result = np.expand_dims(x, -3)", True),
    (9, "result = np.expand_dims(x, 0)", False),
    (9, "result = np.expand_dims(x, 2)", True),
    (10, "result = np.expand_dims(x, -1)", False),
    (11, "result = x[None, :, None]", False),
    (11, "axis = np.newaxis\nresult = x[axis, :, axis]", True),
    (12, "result = np.atleast_1d(np.squeeze(x))", False),
    (12, "result = np.squeeze(x).item() if x.size == 1 else np.squeeze(x)", False),
    (13, "result = np.squeeze(x)", False),
    (14, "result = np.squeeze(x)", False),
    (15, "result = x.reshape(-1)", False),
    (15, "result = np.stack([image.ravel() for image in x])", True),
    (16, "result = x.reshape(x.shape[0], width, height)", False),
    (17, "result = x.transpose(0, 3, 1, 2).reshape(x.shape[0], -1, x.shape[-1])", False),
    (18, "result = x.reshape(0, 6)", False),
    (18, "result = x.reshape(x.shape[0], -1)", False),
    (18, "result = x.reshape(x.shape[0], x.shape[1] * x.shape[-1])", False),
    (18, "batch, height, width = x.shape\nresult = np.reshape(x, (batch, height * width))", True),
])
def test_reshaping_grades_order_axes_and_alternatives(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    graded = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (graded["verdict"] == "Accepted") == accepted, graded
