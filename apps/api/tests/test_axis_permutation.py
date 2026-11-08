from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.axis_permutation import LESSONS
from content.runner import run_payload


def test_axis_permutation_order_copy_constraints_and_old_versions():
    mapped = {1: 1, 2: 3, 3: 7, 4: 9, 5: 6, 6: 8}
    dimensions = {
        1: 2, 2: 3, 3: 3, 4: 3, 5: 3, 6: 4, 7: 3, 8: 3, 9: 4,
        10: 4, 11: 4, 12: 3, 13: 3, 14: 5, 15: 5, 16: 3, 17: 3, 18: 4,
    }
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP04"]
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
            axes_seen = set()
            for case in p["public_tests"] + p["hidden_tests"]:
                env = {}
                exec(case["setup"], env)
                number = lesson["number"]
                value = env["y"] if number == 16 else env["x"]
                assert value.ndim == dimensions[number]
                if number == 4:
                    axes_seen.add(env["axes"])
                    assert sorted(env["axes"]) == list(range(value.ndim))
                if number != 18:
                    assert all(size > 0 for size in value.shape)
                else:
                    assert value.shape[0] == 0
                    assert case["expected"]["shape"] == [
                        0, value.shape[3], value.shape[1], value.shape[2]
                    ]
                    assert case["expected"]["data"] == []
            if lesson["number"] == 4:
                assert len(axes_seen) == 3
        assert questions[16]["public_tests"][0]["expected"]["data"] == [
            [0, 4, 8], [1, 5, 9], [2, 6, 10], [3, 7, 11]
        ]
        restored = questions[15]["public_tests"][0]["expected"]
        assert restored["shape"] == [2, 3, 4]
        assert restored["data"] == [
            [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]],
            [[12, 13, 14, 15], [16, 17, 18, 19], [20, 21, 22, 23]],
        ]
        for old_number, display_number in mapped.items():
            p = questions[display_number - 1]
            assert p["id"] == f"NP04-{old_number:02}"
            previous = f'{p["id"]}@{p["content_version"] - 1}'
            old = ARCHIVED_VARIANTS[(previous, seed)]
            assert problem(previous, seed) == old and old["stage"] == p["stage"]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = x.transpose()", False),
    (2, "result = np.swapaxes(x, 0, 2)", False),
    (3, "result = x.transpose(1, 2, 0)", False),
    (3, "result = np.transpose(x, (2, 0, 1))", True),
    (4, "result = x.transpose(1, 2, 0)", False),
    (4, "result = x.transpose(*axes)", True),
    (5, "result = np.swapaxes(x, 1, 2)", False),
    (6, "result = np.swapaxes(x, 2, 3)", False),
    (6, "result = np.swapaxes(x, -2, -1)", True),
    (6, "result = np.swapaxes(x, -1, 0)", False),
    (7, "result = np.moveaxis(x, 0, -1)", False),
    (8, "result = np.moveaxis(x, -1, 0)", False),
    (9, "result = x.transpose(0, 1, 2, 3).reshape(x.shape[0], x.shape[3], x.shape[1], x.shape[2])", False),
    (10, "result = x.transpose(0, 3, 1, 2)", False),
    (11, "result = np.swapaxes(x, 0, 1)", False),
    (12, "result = np.swapaxes(x, 0, 2)", False),
    (13, "result = x.transpose(2, 1, 0)", False),
    (14, "result = x.transpose(0, 4, 2, 1, 3)", False),
    (15, "result = np.moveaxis(np.moveaxis(x, 0, 1), -1, 2)", False),
    (15, "result = np.moveaxis(x, (4, 0), (2, 1))", True),
    (16, "result = y.transpose(2, 0, 1)", False),
    (17, "result = x.reshape(-1, x.shape[0])", False),
    (17, "result = x.transpose(2, 1, 0).reshape(-1, x.shape[0])", False),
    (17, "result = np.moveaxis(x, 0, -1).reshape(-1, x.shape[0])", True),
    (18, "result = x.transpose(0, 1, 3, 2)", False),
])
def test_axis_permutation_grades_values_and_api_conditions(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    graded = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (graded["verdict"] == "Accepted") == accepted, graded
