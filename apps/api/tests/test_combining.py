from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.combining import LESSONS
from content.runner import run_payload


def test_combining_order_archives_and_boundary_fixtures():
    order = [7, 1, 3, 8, 9, 6, 10, 11, 12, 2, 4, 13, 5, 14, 15, 16, 17, 18]
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP07"]
        assert [p["id"] for p in questions] == [f"NP07-{number:02}" for number in order]
        assert Counter(p["stage"] for p in questions) == {
            "guided": 6, "partial": 6, "independent": 6,
        }
        for p, lesson in zip(questions, LESSONS, strict=True):
            assert p["starter_code"] == "result = "
            assert p["editable_regions"] == [{"start": 9, "end": 9}]
            assert p["hints"] == [lesson["hint"]]
            assert p["public_tests"][0]["setup"] == "import numpy as np\n\n" + lesson["input"]
            assert not {"solution", "hidden_tests"} & public_problem(p).keys()
            if p["content_version"] > 1:
                previous = f'{p["id"]}@{p["content_version"] - 1}'
                old = ARCHIVED_VARIANTS[(previous, seed)]
                restored = problem(previous, seed)
                assert restored["solution"] == old["solution"]
                assert restored["stage"] == p["stage"]

        batch_cases = questions[5]["public_tests"] + questions[5]["hidden_tests"]
        batch_counts = set()
        for case in batch_cases:
            env = {}
            exec(case["setup"], env)
            batch_counts.add(len(env["batches"]))
        assert batch_counts == {1, 2, 3}

        empty_cases = questions[16]["public_tests"] + questions[16]["hidden_tests"]
        empty_sides = set()
        for case in empty_cases:
            env = {}
            exec(case["setup"], env)
            a, b = env["a"], env["b"]
            empty_sides.add((len(a) == 0, len(b) == 0))
            assert case["expected"]["shape"] == [len(a) + len(b), a.shape[1]]
        assert empty_sides == {(True, False), (False, True), (True, True)}

        pairs = public_problem(questions[17])["public_tests"][0]
        features, labels = pairs["expected"]
        assert pairs["expected_tuple_paths"] == [[]]
        assert features["shape"] == [5, 2]
        assert labels["shape"] == [5] and labels["data"] == [0, 1, 1, 0, 1]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = np.concatenate([b, a])", False),
    (2, "result = np.concatenate([a, b], axis=1)", False),
    (3, "result = np.concatenate([a, b], axis=-1)", True),
    (4, "result = np.concatenate([a.ravel(), b])", False),
    (4, "result = np.concatenate([a.ravel(order='F'), b], axis=None)", False),
    (4, "result = np.concatenate((a, b), None)", True),
    (6, "result = np.concatenate(batches[:1])", False),
    (7, "result = np.vstack([b, a])", False),
    (8, "result = np.vstack([a, b]).T", False),
    (9, "result = np.concatenate([x, extra[:, None]], axis=-1)", True),
    (10, "result = np.stack([a, b], axis=1)", False),
    (11, "result = np.stack([a, b], axis=0)", False),
    (12, "result = np.stack([original, transformed], axis=-1)", False),
    (13, "result = np.stack([b, g, r], axis=-1)", False),
    (14, "result = np.stack([r, g, b], axis=-1).squeeze(-2)", False),
    (15, "result = np.concatenate([extra, base], axis=1)", False),
    (16, "result = np.stack([c, b, a])", False),
    (17, "result = np.concatenate([a, b], axis=None)", False),
    (18, "result = [np.concatenate([x_a, x_b]), np.concatenate([y_a, y_b])]", False),
    (18, "result = (np.concatenate([x_a, x_b]), np.concatenate([y_b, y_a]))", False),
    (18, "result = (np.concatenate([x_a, x_b]), np.concatenate([y_a, y_b])[:, None])", False),
])
def test_combining_grades_axis_order_api_and_tuple_type(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    result = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"])
    assert (result["verdict"] == "Accepted") == accepted, result
