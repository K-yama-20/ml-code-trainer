from collections import Counter

import pytest

from apps.api.app.content import ARCHIVED_VARIANTS, DISPLAY, VARIANTS, problem, public_problem
from apps.api.app.grading import judge
from content.broadcasting import LESSONS
from content.runner import run_payload


def test_broadcasting_order_editor_input_constraints_and_archived_types():
    mapped = {1: 3, 2: 7, 3: 6, 4: 8, 5: 11, 6: 9}
    for seed, catalog in VARIANTS.items():
        questions = [p for p in catalog["problems"] if p["concept_id"] == "NP06"]
        assert len(questions) == 18
        assert [p["id"] for p in questions] == [lesson["id"] for lesson in LESSONS]
        assert Counter(p["stage"] for p in questions) == dict.fromkeys(
            ("guided", "partial", "independent"), 6
        )
        for number, (p, lesson) in enumerate(zip(questions, LESSONS, strict=True), 1):
            assert (p["title"], p["description"], p["hints"], p["solution"]) == (
                lesson["title"], lesson["task"], [lesson["hint"]], lesson["solution"]
            )
            assert p["workspace"]["provided_code"] == (
                "import numpy as np\n\n" + lesson["input"] + "\n\n# 以下に答えを記入"
            )
            assert p["starter_code"] == "result = "
            assert p["editable_regions"] == [{"start": 9, "end": 9}]
            assert p["protect_inputs"] and p["execution"]["result_type"] == "array"
            assert p["required_ast"] == ("call:broadcast_to" if number == 17 else "")
            assert not {"solution", "hidden_tests", "hints"} & public_problem(p).keys()
            cases = p["public_tests"] + p["hidden_tests"]
            axes_seen = []
            for case in cases:
                env = {}
                exec(case["setup"], env)
                expected = case["expected"]
                assert expected["kind"] == "array"
                if number in (1, 3, 4, 5, 6, 10, 11, 12, 13, 15, 16):
                    x = env["x"]
                    assert x.ndim == (4 if number in (15, 16) else 2)
                    assert expected["shape"] == list(x.shape)
                if number in (3, 4, 5, 6):
                    values = env["bias"] if number in (3, 5) else env["weights"]
                    assert values.ndim == 1
                    assert len(values) == x.shape[1 if number in (3, 4) else 0]
                    assert x.shape[0] != x.shape[1]
                if number == 2:
                    pixels = env["pixels"]
                    assert pixels.ndim == 2 and ((pixels >= 0) & (pixels <= 255)).all()
                if number == 7:
                    r, c = env["row_values"], env["col_values"]
                    assert r.shape[1] == c.shape[0] == 1
                    assert expected["shape"] == [len(r), c.shape[1]]
                if number in (8, 9):
                    assert env["a"].ndim == env["b"].ndim == 1
                    assert len(env["a"]) != len(env["b"])
                    assert expected["shape"] == [len(env["a"]), len(env["b"])]
                if number == 12:
                    assert (x.sum(axis=1) > 0).all()
                if number == 13:
                    assert env["means"].shape == env["stds"].shape == (x.shape[1],)
                    assert (env["stds"] > 0).all()
                if number == 14:
                    assert env["image"].ndim == 3
                    assert env["bias"].shape == (env["image"].shape[2],)
                if number in (15, 16):
                    assert (env["bias"] if number == 15 else env["weights"]).shape == (
                        x.shape[1 if number == 15 else 0],
                    )
                if number == 17:
                    assert expected["shape"] == [env["rows"], env["values"].size]
                    axes_seen.append((env["rows"], env["values"].size))
                if number == 18:
                    a, b = env["points"], env["centers"]
                    assert a.ndim == b.ndim == 2 and a.shape[1] == b.shape[1]
                    assert len(a) != len(b)
                    assert expected["shape"] == [len(a), len(b)]
                    axes_seen.append(a.shape[1])
            if number in (17, 18):
                assert len(set(axes_seen)) == 3
        assert questions[17]["public_tests"][0]["expected"]["data"] == [[1., 8.], [2., 1.], [9., 2.]]
        for old_number, display_number in mapped.items():
            p = questions[display_number - 1]
            assert p["id"] == f"NP06-{old_number:02}"
            previous = f'{p["id"]}@{p["content_version"] - 1}'
            old = ARCHIVED_VARIANTS[(previous, seed)]
            restored = problem(previous, seed)
            assert old["stage"] == p["stage"] and restored["solution"] == old["solution"]
            for field in ("public_tests", "hidden_tests"):
                for i, case in enumerate(restored[field]):
                    assert {k: v for k, v in case.items() if k != "expected_tuple_paths"} == old[field][i]
                    assert case["expected_tuple_paths"] == DISPLAY[f"{previous}:{seed}"][field][i]


@pytest.mark.parametrize(("number", "code", "accepted"), [
    (1, "result = x", False),
    (1, "result = np.add(offset, x)", True),
    (1, "result = x + offset\nx[:] = 0", False),
    (2, "result = pixels / np.max(pixels)", False),
    (3, "result = x + bias[:, None]", False),
    (3, "result = x + bias\nbias[:] = 0", False),
    (4, "result = x * weights[:, None]", False),
    (5, "result = x + bias", False),
    (5, "result = x + bias.reshape(-1, 1)", True),
    (6, "result = x * weights", False),
    (6, "result = np.multiply(x, np.expand_dims(weights, 1))", True),
    (7, "result = (row_values + col_values).T", False),
    (8, "result = np.outer(b, a)", False),
    (8, "result = np.outer(a, b)", True),
    (9, "result = b[None, :] - a[:, None]", False),
    (10, "result = x - np.mean(x)", False),
    (10, "result = x - np.mean(x, axis=1, keepdims=True)", False),
    (11, "result = x - np.mean(x, axis=0, keepdims=True)", False),
    (11, "result = x - x.mean(axis=1).reshape(-1, 1)", True),
    (12, "result = x / x.sum(axis=0)", False),
    (13, "result = x - means / stds", False),
    (14, "result = image + bias[:, None, None]", False),
    (15, "result = x + bias", False),
    (15, "result = x + bias.reshape(1, -1, 1, 1)", True),
    (16, "result = x * weights", False),
    (16, "result = x * weights.reshape(-1, 1, 1, 1)", True),
    (17, "result = np.tile(values, (rows, 1))", False),
    (17, "result = np.broadcast_to(values, (4, 3))", False),
    (17, "result = np.broadcast_to(values, (rows, len(values)))", True),
    (18, "result = np.sqrt(((points[:, None] - centers[None, :]) ** 2).sum(axis=-1))", False),
    (18, "result = ((points[:, None] - centers[None, :]) ** 2).sum(axis=0)", False),
    (18, "result = ((centers[:, None] - points[None, :]) ** 2).sum(axis=-1)", False),
    (18, "result = ((points[:, None] - centers[None, :]) ** 2).mean(axis=-1)", False),
    (18, "result = ((points[:, None] - centers[None, :]) ** 2).sum(axis=-1)", True),
])
def test_broadcasting_grades_axes_distance_input_protection_and_alternatives(number, code, accepted):
    p = problem(LESSONS[number - 1]["id"])
    cases = p["public_tests"] + p["hidden_tests"]
    output = run_payload({"code": code, "cases": cases, "execution": p["execution"]})
    result = judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"], p["protect_inputs"])
    assert (result["verdict"] == "Accepted") == accepted, result
