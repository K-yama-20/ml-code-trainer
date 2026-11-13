import json
from collections import Counter

import numpy as np
import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.conditional import LESSONS
from content.runner import run_browser_payload, run_payload


def test_conditional_order_archives_and_display_examples():
    order = [1, 7, 3, 8, 9, 10, 11, 2, 12, 13, 14, 15, 4, 16, 5, 17, 6, 18]
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP08"]
        assert [p["id"] for p in questions] == [f"NP08-{number:02}" for number in order]
        assert Counter(p["stage"] for p in questions) == {
            "guided": 6, "partial": 6, "independent": 6,
        }
        for p, lesson in zip(questions, LESSONS, strict=True):
            setup = "import numpy as np\n\n" + lesson["input"]
            assert p["public_tests"][0]["setup"] == setup
            assert p["workspace"]["provided_code"] == setup + "\n\n# 以下に答えを記入"
            assert p["starter_code"] == "result = "
            assert p["editable_regions"] == [{"start": 9, "end": 9}]
            assert p["hints"] == [lesson["hint"]]
            assert not {"solution", "hidden_tests"} & public_problem(p).keys()
            if p["content_version"] > 1:
                previous = f'{p["id"]}@{p["content_version"] - 1}'
                old = ARCHIVED_VARIANTS[(previous, seed)]
                restored = problem(previous, seed)
                assert restored["solution"] == old["solution"]
                assert restored["stage"] == p["stage"]

        examples = [p["public_tests"][0]["expected"] for p in questions]
        assert examples[2]["dtype"] == "int64"
        assert examples[11]["dtype"] == "uint8"
        assert examples[14]["data"] == [0.0, 1.5, "__Inf__", "__-Inf__", -2.0]
        assert examples[15]["data"] == [0.0, 4.0, 5.0, -5.0, -7.0]
        assert examples[17]["data"] == [3.0, 0.0, 0.0, -2.0]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = np.maximum(x, 0)", False),
    (2, "result = np.where(use_a, b, a)", False),
    (3, "result = (x > threshold).astype(np.int64)", False),
    (3, "result = (x >= threshold).astype(np.int32)", False),
    (3, "result = np.where(x >= threshold, 1, 0).astype('int64')", True),
    (4, "result = np.where((x > lower) & (x < upper), x, fallback)", False),
    (5, "result = np.where(scores <= lower, 0, np.where(scores <= upper, 1, 2))", False),
    (6, "result = np.maximum(a.max(), b.max())", False),
    (7, "result = np.minimum(requested, available.sum())", False),
    (8, "result = np.clip(x, 0, None)", False),
    (9, "result = np.clip(x, lower, 6)", False),
    (10, "result = np.clip(x, -8, upper)", False),
    (11, "result = np.clip(x, lower.min(), upper.max())", False),
    (12, "result = np.clip(pixels.astype(np.uint8), 0, 255)", False),
    (12, "result = np.clip(pixels, 0, 255)", False),
    (13, "result = ((pred - target) ** 2).mean(axis=1)", False),
    (14, "result = np.where(valid, 0.0, (pred - target) ** 2)", False),
    (15, "result = np.nan_to_num(x)", False),
    (16, "result = np.clip(np.nan_to_num(x, nan=0., posinf=high, neginf=low), low, high)", False),
    (17, "result = np.log10(np.clip(x, eps, None))", False),
    (18, """mask = denominator != 0
result = np.zeros_like(numerator)
result[mask] = np.divide(numerator[mask], denominator[mask])""", True),
])
def test_conditional_grades_boundaries_dtype_and_special_values(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    result = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"])
    assert (result["verdict"] == "Accepted") == accepted, result


def test_masking_after_division_fails_and_numpy_error_policy_is_restored():
    p = problem("NP08-18")
    cases = p["public_tests"] + p["hidden_tests"]
    code = "result = np.where(denominator != 0, np.divide(numerator, denominator), 0.)"
    payload = {"code": code, "cases": cases, "execution": p["execution"]}
    with np.errstate(divide="ignore", invalid="ignore"):
        original_policy = np.geterr()
        unchecked = run_payload({**payload, "execution": {**p["execution"], "strict_division": False}})
        assert judge(unchecked["outputs"], cases, code, p["required_ast"])["verdict"] == "Accepted"

        checked = json.loads(run_browser_payload(json.dumps(payload), p["required_ast"]))
        assert all(output["kind"] == "FloatingPointError" for output in checked["outputs"])
        assert judge(checked["outputs"], cases, code, p["required_ast"])["verdict"] == "Runtime Error"
        assert np.geterr() == original_policy
