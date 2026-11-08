from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.reductions import LESSONS
from content.runner import run_payload


def test_reductions_order_editor_shapes_and_archives():
    mapped = {1: 5, 2: 11, 3: 4, 4: 12, 5: 15, 6: 17}
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP05"]
        assert len(questions) == 18
        assert [p["id"] for p in questions] == [lesson["id"] for lesson in LESSONS]
        assert Counter(p["stage"] for p in questions) == dict.fromkeys(
            ("guided", "partial", "independent"), 6
        )
        for number, (p, lesson) in enumerate(zip(questions, LESSONS, strict=True), 1):
            assert p["title"] == lesson["title"] and p["description"] == lesson["task"]
            assert p["solution"] == lesson["solution"] and p["hints"] == [lesson["hint"]]
            assert p["workspace"]["provided_code"] == (
                "import numpy as np\n\n" + lesson["input"] + "\n\n# 以下に答えを記入"
            )
            assert p["starter_code"] == "result = "
            assert p["editable_regions"] == [{"start": 9, "end": 9}]
            assert not {"solution", "hidden_tests", "hints"} & public_problem(p).keys()
            assert p["protect_inputs"] == (number == 17)
            cases = p["public_tests"] + p["hidden_tests"]
            shapes = []
            for case in cases:
                env = {}
                exec(case["setup"], env)
                x = env["x"]
                assert x.ndim == (3 if number == 14 else 4 if number in (15, 16) else 2)
                shapes.append(x.shape)
                if number == 18:
                    assert x.shape[0] == 0
                    assert case["expected"]["shape"] == [x.shape[1]]
                    assert case["expected"]["data"] == [0] * x.shape[1]
                else:
                    assert all(size > 0 for size in x.shape)
                if number in (11, 12, 13, 15, 16):
                    expected_shape = {
                        11: [1, x.shape[1]], 12: [x.shape[0], 1], 13: [1, 1],
                        15: list(x.shape[:2]), 16: list(x.shape[:2]) + [1, 1],
                    }[number]
                    assert case["expected"]["shape"] == expected_shape
            assert len(set(shapes)) == 3
            if number in (15, 16):
                assert any(shape[0] == 1 for shape in shapes)
                assert any(shape[1] == 1 for shape in shapes)
                assert any(shape[2] != shape[3] for shape in shapes)
        assert questions[8]["public_tests"][0]["expected"]["data"] == [1, 0]
        assert questions[9]["public_tests"][0]["expected"]["data"] == [1.0, 2.0, 3.0]
        for old_number, display_number in mapped.items():
            p = questions[display_number - 1]
            assert p["id"] == f"NP05-{old_number:02}"
            previous = f'{p["id"]}@{p["content_version"] - 1}'
            old = ARCHIVED_VARIANTS[(previous, seed)]
            assert problem(previous, seed) == old and old["stage"] == p["stage"]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = np.sum(x, axis=0)", False),
    (1, "result = np.asarray(np.sum(x))", False),
    (1, "result = np.sum(x) * 0 + 21", False),
    (1, "result = x.sum()", True),
    (2, "result = np.mean(x, axis=1)", False),
    (3, "result = np.sum(x, axis=0)", False),
    (4, "result = np.sum(x, axis=1)", False),
    (5, "result = np.mean(x, axis=0)", False),
    (5, "result = x.sum(axis=-1) / x.shape[-1]", True),
    (6, "result = np.mean(x, axis=1)", False),
    (7, "result = np.max(x, axis=0)", False),
    (8, "result = np.min(x, axis=1)", False),
    (9, "result = np.max(x, axis=1)", False),
    (9, "result = x.shape[1] - 1 - np.argmax(x[:, ::-1], axis=1)", False),
    (9, "result = x.argmax(axis=-1)", True),
    (10, "result = np.std(x, axis=0)", False),
    (10, "result = np.std(x, axis=0, ddof=1)", False),
    (10, "d = 0\nresult = x.std(axis=0, ddof=d)", True),
    (10, "result = np.std(x, axis=0, ddof=0.0)", True),
    (11, "result = np.sum(x, axis=0)", False),
    (11, "result = np.sum(x, axis=0)[None, :]", False),
    (11, "options = {'keepdims': True}\nresult = x.sum(axis=0, **options)", True),
    (12, "result = np.max(x, axis=1)", False),
    (12, "result = x.max(axis=-1, keepdims=True)", True),
    (13, "result = np.mean(x)", False),
    (13, "result = np.mean(x, axis=0, keepdims=True)", False),
    (14, "result = np.mean(x, axis=(0, 2))", False),
    (14, "result = x.mean(axis=(-1, -2))", True),
    (15, "result = np.mean(x, axis=(2, 3)).squeeze()", False),
    (15, "result = np.mean(x, axis=(1, 3))", False),
    (16, "result = np.mean(x, axis=(2, 3))", False),
    (16, "result = np.mean(x, axis=(2, 3))[:, :, None, None]", False),
    (16, "keep = True\nresult = x.mean(axis=(-2, -1), keepdims=keep)", True),
    (16, "result = x.sum(axis=(2, 3), keepdims=True) / (x.shape[2] * x.shape[3])", True),
    (17, "result = x - np.mean(x, axis=0)", False),
    (17, "x -= np.mean(x)\nresult = x", False),
    (17, "saved = x.copy()\nx.shape = (x.size,)\nresult = saved - saved.mean()", False),
    (17, "saved = x.copy()\nx.dtype = np.int32\nresult = saved - saved.mean()", False),
    (17, "result = np.subtract(x, x.sum() / x.size)", True),
    (18, "result = np.sum(x, axis=1)", False),
    (18, "result = np.sum(x, axis=0, keepdims=True)", False),
    (18, "result = x.sum(axis=0).tolist()", False),
])
def test_reductions_grades_axes_options_types_and_input_protection(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    graded = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (graded["verdict"] == "Accepted") == accepted, graded
