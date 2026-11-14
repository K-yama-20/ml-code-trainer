"""Compile NP07 from authored examples and independently assembled arrays."""

import ast
import json
from pathlib import Path

import numpy as np

from content.runner import pack_expected

CONCEPT_ID = "NP07"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

VECTOR_PAIRS = [
    "a = np.array([-4, 1, 5, 9])\nb = np.array([7, 0, -2, 4])",
    "a = np.array([0.5])\nb = np.array([-3.5])",
]
MATRIX_PAIRS = [
    "a = np.arange(12).reshape(3, 4)\nb = (np.arange(12) + 20).reshape(3, 4)",
    "a = np.array([[3], [-4]])\nb = np.array([[12], [7]])",
]
RGB = [
    "r = np.arange(12).reshape(3, 4)\ng = r + 20\nb = r + 40",
    "r = np.array([[3, 8, 17]])\ng = r + 50\nb = r + 100",
]
ALTERNATIVES = {
    1: ["a = np.array([-3])\nb = np.array([7, 8, 0, -5])",
        "a = np.array([9.5, 1.5])\nb = np.array([-1.0])"],
    2: ["a = np.array([[0, -2]])\nb = np.arange(6).reshape(3, 2)",
        "a = np.arange(8).reshape(2, 4)\nb = np.array([[20, 21, 22, 23]])"],
    3: ["a = np.array([[9], [7], [-4]])\nb = np.arange(6).reshape(3, 2)",
        "a = np.array([[5, -1, 8]])\nb = np.array([[10, -2]])"],
    4: ["a = np.arange(12).reshape(3, 4).T\nb = np.array([-2, 9])",
        "a = np.array([[1], [7], [9]])\nb = np.array([0.5])"],
    5: ["first = np.arange(12).reshape(1, 3, 4)\nsecond = np.arange(12, 20).reshape(1, 2, 4)",
        "first = np.arange(6).reshape(3, 2, 1)\nsecond = np.arange(6, 18).reshape(3, 4, 1)"],
    6: ["batches = [np.array([[9, -4, 7], [2, 0, 8]])]",
        "batches = [np.array([[8], [2], [3]]), np.array([[-1], [4]])]"],
    7: VECTOR_PAIRS,
    8: VECTOR_PAIRS,
    9: ["x = np.arange(8).reshape(2, 4)\nextra = np.array([-3, 2])",
        "x = np.array([[2], [-6], [9], [4]])\nextra = np.array([1, 5, 3, 0])"],
    10: MATRIX_PAIRS,
    11: MATRIX_PAIRS,
    12: ["original = np.arange(12).reshape(3, 4)\ntransformed = (np.arange(12) + 20).reshape(3, 4)",
         "original = np.array([[3], [-4]])\ntransformed = np.array([[12], [7]])"],
    13: RGB,
    14: [fixture + "\nr = r[..., None]\ng = g[..., None]\nb = b[..., None]"
         for fixture in RGB],
    15: ["base = np.arange(24).reshape(1, 2, 3, 4)\nextra = np.arange(24, 36).reshape(1, 1, 3, 4)",
         "base = np.arange(6).reshape(3, 1, 1, 2)\nextra = np.arange(6, 24).reshape(3, 3, 1, 2)"],
    16: ["a = np.array(-2)\nb = np.array(0)\nc = np.array(4)",
         "a = np.array(1.5)\nb = np.array(-3.0)\nc = np.array(2.5)"],
    17: ["a = np.array([[7, -1], [3, 4]])\nb = np.empty((0, 2), dtype=int)",
         "a = np.empty((0, 4))\nb = np.empty((0, 4))"],
    18: ["x_a = np.array([[9, 0, -5]])\ny_a = np.array([3])\nx_b = np.arange(6).reshape(2, 3)\ny_b = np.array([4, 2])",
         "x_a = np.array([[2], [-3], [8]])\ny_a = np.array([1, 2, 0])\nx_b = np.array([[9]])\ny_b = np.array([4])"],
}


def join_blocks(arrays, axis):
    shape = list(arrays[0].shape)
    shape[axis] = sum(array.shape[axis] for array in arrays)
    result = np.empty(shape, dtype=np.result_type(*arrays))
    start = 0
    for array in arrays:
        stop = start + array.shape[axis]
        region = [slice(None)] * result.ndim
        region[axis] = slice(start, stop)
        result[tuple(region)] = array
        start = stop
    return result


def expected_combination(number, inputs):
    if number in (1, 2, 3, 5, 14, 15, 17):
        axis = {3: 1, 5: 1, 14: 2, 15: 1}.get(number, 0)
        return join_blocks(inputs, axis)
    if number == 4:
        a, b = inputs
        return np.array([*a.flat, *b])
    if number == 6:
        return join_blocks(inputs[0], 0)
    if number == 8:
        return np.array(list(zip(*inputs, strict=True)))
    if number == 9:
        x, extra = inputs
        return join_blocks((x, extra[:, None]), 1)
    if number == 18:
        x_a, y_a, x_b, y_b = inputs
        return join_blocks((x_a, x_b), 0), join_blocks((y_a, y_b), 0)

    # Build the new axis first, then move it into the requested position.
    axis = {7: 0, 10: 0, 11: -1, 12: 1, 13: -1, 16: 0}[number]
    rows = np.array([array.tolist() for array in inputs])
    return np.moveaxis(rows, 0, axis)


def compile_combining(concept, seed):
    for lesson in LESSONS:
        number = lesson["number"]
        pid, version, stage = lesson["id"], lesson["version"], lesson["stage"]
        inputs = [target.id for node in ast.parse(lesson["input"]).body
                  for target in node.targets if isinstance(target, ast.Name)]
        tests = []
        for fixture in [lesson["input"], *ALTERNATIVES[number][::(-1 if seed == 99 else 1)]]:
            setup = "import numpy as np\n\n" + fixture
            env = {}
            exec(setup, env)
            value = expected_combination(number, [env[name] for name in inputs])
            tests.append({"setup": setup, "args": ", ".join(inputs), **pack_expected(value)})
        api = {7: "vstack", 8: "column_stack"}.get(number, "concatenate")
        if number in (10, 11, 12, 13, 16):
            api = "stack"
        required = f"call:{api}"
        if number == 4:
            required = "call-keywords:" + json.dumps({
                "name": api, "keywords": {"axis": None}, "positions": {"axis": 1},
            })
        provided = "import numpy as np\n\n" + lesson["input"] + "\n\n# 以下に答えを記入"
        yield {
            "id": pid, "family_id": pid, "version_id": f"{pid}@{version}",
            "content_version": version, "concept_id": CONCEPT_ID, "module_id": "numpy",
            "stage": stage, "type": "implementation",
            "difficulty": ("guided", "partial", "independent").index(stage) + 1,
            "title": lesson["title"], "description": lesson["task"],
            "learning_goal": concept["description"], "input_conditions": "",
            "output_conditions": lesson["task"], "starter_code": PREFIX, "example": provided,
            "editable_regions": [{"start": len(PREFIX), "end": len(PREFIX)}],
            "hints": [lesson["hint"]], "solution": lesson["solution"],
            "explanation": lesson["hint"], "common_mistakes": [],
            "public_tests": tests[:2], "hidden_tests": tests[2:],
            "required_ast": required, "check_dtype": False, "protect_inputs": False,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "combining-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": inputs, "globals": ["np"],
                "allow_input_mutation": True, "result_type": "tuple" if number == 18 else "array",
            },
        }
