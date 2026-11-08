from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.indexing import LESSONS
from content.runner import run_payload


def test_indexing_order_authored_copy_inputs_and_old_versions():
    mapped = {1: 7, 2: 9, 3: 13, 4: 10, 5: 11, 6: 17}
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP02"]
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
                if lesson["number"] == 1:
                    assert 0 <= env["index"] < len(env["x"])
                if lesson["number"] == 5:
                    assert 0 <= env["row"] < env["x"].shape[0]
                    assert 0 <= env["col"] < env["x"].shape[1]
                if lesson["number"] in (7, 8):
                    assert 0 <= env["col"] < env["x"].shape[1]
                if lesson["number"] == 16:
                    assert len(env["labels"]) == env["x"].shape[0]
        for old_number, display_number in mapped.items():
            p = questions[display_number - 1]
            assert p["id"] == f"NP02-{old_number:02}"
            previous = f'{p["id"]}@{p["content_version"] - 1}'
            old = ARCHIVED_VARIANTS[(previous, seed)]
            assert problem(previous, seed) == old and old["stage"] == p["stage"]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = 30", False),
    (1, "result = np.take(x, index)", True),
    (2, "result = x[len(x) - 1]", False),
    (3, "result = x[start:stop + 1]", False),
    (4, "result = np.flip(x)", False),
    (5, "result = x[col, row]", False),
    (7, "result = x[:, col:col + 1]", False),
    (8, "result = x[:, col]", False),
    (8, "result = x[:, [col]]", True),
    (9, "result = x[row_start:row_stop + 1, col_start:col_stop + 1]", False),
    (10, "result = x[1::2, :]", False),
    (11, "result = x[:, sorted(set(columns))]", False),
    (11, "result = np.take(x, columns, axis=1)", True),
    (12, "result = (x >= threshold).astype(np.int64)", False),
    (13, "result = x[x > threshold]", False),
    (14, "result = x[(x >= lower) & (x <= upper)]", False),
    (15, "result = x[(x <= lower) | (x >= upper)]", False),
    (16, "result = np.array([row for row, label in zip(x, labels) if label == target])", False),
    (17, "result = x[np.isfinite(x)]", False),
    (17, "result = x[x == x]", True),
    (18, "result = np.where(x >= threshold, x, 0)", False),
    (18, "result = x.T[x.T >= threshold]", False),
])
def test_indexing_grades_shapes_boundaries_and_alternatives(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    graded = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (graded["verdict"] == "Accepted") == accepted, graded
