from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.arrays import LESSONS
from content.runner import run_payload


def test_array_order_authored_copy_fixed_inputs_and_old_versions():
    mapped = {1: 3, 2: 4, 3: 12, 4: 9, 5: 17, 6: 15}
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP01"]
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
            if lesson["number"] in (2, 17, 18):
                for case in p["public_tests"] + p["hidden_tests"]:
                    env = {}
                    exec(case["setup"], env)
                    if lesson["number"] == 2:
                        assert env["np"].shape(env["values"]) == (2, 3)
                    elif lesson["number"] == 17:
                        assert env["x"].shape == ()
                        assert case["expected"] == [[], 0, 1]
                    else:
                        assert env["x"].shape == (0, 4)
                        assert case["expected"] == [[0, 4], 2, 0]
        for old_number, display_number in mapped.items():
            p = questions[display_number - 1]
            assert p["id"] == f"NP01-{old_number:02}"
            previous = f'{p["id"]}@{p["content_version"] - 1}'
            old = ARCHIVED_VARIANTS[(previous, seed)]
            assert problem(previous, seed) == old and old["stage"] == p["stage"]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = np.array([3, -1, 5, 0])", False),
    (2, "result = np.array(values).ravel()", False),
    (3, "result = np.array(values, dtype='float64')", False),
    (3, "result = np.array(values, dtype='float32')", True),
    (4, "result = [*x.shape]", False),
    (7, "result = x.shape[1]", False),
    (8, "result = str(x.dtype)", True),
    (9, "result = np.zeros((rows, cols), dtype=np.float32)", False),
    (9, "result = np.zeros(shape=(rows, cols), dtype='float64')", True),
    (10, "result = np.ones(shape, dtype=np.float64)", False),
    (11, "result = np.full(shape, initial_value, dtype=np.float64)", False),
    (12, "result = np.arange(0, stop + 1, step, dtype=np.int64)", False),
    (12, "result = np.arange(0, stop, step, dtype=np.int32)", False),
    (13, "result = np.linspace(start, stop, num=num, endpoint=False)", False),
    (14, "result = np.zeros_like(x, dtype=np.float64)", False),
    (14, "saved = x.copy()\nx[:] = 0\nresult = np.zeros_like(saved)", False),
    (14, "saved = x.copy()\nx.shape = (x.size,)\nresult = np.zeros_like(saved)", False),
    (15, "saved = x.copy()\nx.dtype = np.float32\nresult = saved.astype(np.float64)", False),
    (15, "saved = x.copy()\nx[:] = 0\nresult = saved.astype(np.float64)", False),
    (16, "result = np.floor(x).astype(np.int32)", False),
    (16, "saved = x.copy()\nx[:] = 0\nresult = saved.astype(np.int32)", False),
    (17, "result = ((), 0, 1)", False),
    (17, "shape = ()\nndim = 0\nsize = 1\nresult = (shape, ndim, size)", False),
    (17, "result = (x.shape, x.size, x.ndim)", False),
    (18, "result = ((0, 4), 2, 0)", False),
    (18, "result = (x.shape, 2, x.size)", False),
    (18, "shape = x.shape\naxes = x.ndim\ncount = x.size\nresult = (shape, axes, count)", True),
])
def test_array_grading_rejects_errors_and_accepts_valid_alternatives(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    result = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    graded = judge(result["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (graded["verdict"] == "Accepted") == accepted, graded
