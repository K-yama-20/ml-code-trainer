"""NP09 and the pandas/scikit-learn/PyTorch drills compiled by content.ordered."""

from collections import Counter

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import equivalent, judge
from content.runner import run_payload
from scripts.compile_content import AUTHORED_MODULES


def grade(p, code):
    cases = p["public_tests"] + p["hidden_tests"]
    out = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    return judge(out["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])


def test_authored_order_stages_runtime_and_archived_versions():
    assert len(AUTHORED_MODULES) == 19
    for module, _ in AUTHORED_MODULES:
        for seed, catalog in VARIANTS.items():
            questions = [p for p in catalog["problems"] if p["concept_id"] == module.CONCEPT_ID]
            assert [p["id"] for p in questions] == [lesson["id"] for lesson in module.LESSONS]
            assert Counter(p["stage"] for p in questions) == {"guided": 6, "partial": 6, "independent": 6}
            for p, lesson in zip(questions, module.LESSONS, strict=True):
                assert p["runtime"] == ("sandbox" if p["module_id"] == "pytorch" else "browser")
                assert p["hints"] == [lesson["hint"]]
                assert p["public_tests"][0]["setup"] + "\n\n# 以下に答えを記入" == p["workspace"]["provided_code"]
                assert not {"solution", "hidden_tests"} & public_problem(p).keys()
                if p["content_version"] > 1:
                    # Earlier submissions and drafts still resolve the old version.
                    previous = f'{p["id"]}@{p["content_version"] - 1}'
                    assert ARCHIVED_VARIANTS[(previous, seed)]["version_id"] == previous
                    assert problem(previous, seed)["version_id"] == previous


def test_relative_comparison_rejects_rounding_tiny_values_to_zero():
    expected = {"kind": "array", "shape": [2], "dtype": "float64", "data": [1e-16, 2.0]}
    rounded = {"kind": "array", "shape": [2], "dtype": "float64", "data": [0.0, 2.0]}
    assert equivalent(rounded, expected)
    assert not equivalent(rounded, expected, relative=True)
    p = problem("NP09-13@1")
    assert all(case["comparison"] == "relative" for case in p["public_tests"] + p["hidden_tests"])
    assert grade(p, "result = np.log1p(x)")["verdict"] == "Accepted"
    assert grade(p, "result = np.log(1 + x)")["verdict"] == "Wrong Answer"


def test_strict_overflow_rejects_saturating_formulas():
    p = problem("NP09-15@1")
    assert p["execution"]["strict_overflow"]
    stable = "z = np.exp(-np.abs(x))\nresult = np.where(x >= 0, 1 / (1 + z), z / (1 + z))"
    assert grade(p, stable)["verdict"] == "Accepted"
    naive = grade(p, "result = 1 / (1 + np.exp(-x))")
    assert naive["verdict"] == "Runtime Error" and "overflow" in naive["stderr"]
