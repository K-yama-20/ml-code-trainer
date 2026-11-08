"""Compile the authored NP03 reshape, expand_dims and squeeze exercises."""

import ast
import json
from pathlib import Path

from content.runner import pack_expected

CONCEPT_ID = "NP03"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

ALTERNATIVES = {
    1: ["x = np.array([-2, 0, 5, 9, 1, 3, 4, 8])\nrows = 4\ncols = 2",
        "x = np.array([], dtype=np.float32)\nrows = 0\ncols = 4"],
    2: ["x = np.arange(10)\nwidth = 2", "x = np.array([], dtype=np.float32)\nwidth = 3"],
    3: ["x = np.arange(10)\nrows = 2", "x = np.arange(6)\nrows = 1"],
    4: ["x = np.array([[9, 0], [-1, 8], [3, 7]])", "x = np.zeros((0, 4))"],
    5: ["x = np.array([-3, 0, 2, 8])", "x = np.array([], dtype=np.int32)"],
    6: ["x = np.array([9, -2])", "x = np.array([], dtype=np.float32)"],
    7: ["x = np.array(-2.5)", "x = np.array(0, dtype=np.int16)"],
    8: ["x = np.array([[1], [2], [3]])", "x = np.zeros((0, 4))"],
    9: ["x = np.array([[1, 4], [2, 5], [3, 6]])", "x = np.zeros((0, 2))"],
    10: ["x = np.array([[9, 0, -2, 7]])", "x = np.array([[1, 2], [3, 4], [5, 6]])"],
    11: ["x = np.array([-3, 2, 7, 1])", "x = np.array([], dtype=np.float32)"],
    12: ["x = np.array([[[[9]]]])", "x = np.arange(6).reshape(1, 2, 1, 3, 1)"],
    13: ["x = np.array([[[9]]])", "x = np.arange(4).reshape(1, 4, 1)"],
    14: ["x = np.arange(4).reshape(2, 2, 1)", "x = np.array([[[9]]])"],
    15: ["x = np.arange(12).reshape(1, 3, 4)", "x = np.arange(12).reshape(3, 2, 2)"],
    16: ["x = np.arange(8).reshape(1, 8)\nheight = 4\nwidth = 2",
         "x = np.arange(12).reshape(3, 4)\nheight = 1\nwidth = 4"],
    17: ["x = np.arange(24).reshape(1, 2, 3, 4)", "x = np.arange(12).reshape(3, 2, 2, 1)"],
    18: ["x = np.zeros((0, 3, 4), dtype=np.float32)", "x = np.zeros((0, 1, 5), dtype=np.int16)"],
}

# Target shapes are specified independently of the reference expressions.
ORACLES = {
    1: "np.reshape(x, (rows, cols))",
    2: "np.reshape(x, (x.size // width, width))",
    3: "np.reshape(x, (rows, x.size // rows))",
    4: "np.ravel(x, order='C')",
    5: "np.expand_dims(x, axis=0)",
    6: "np.expand_dims(x, axis=1)",
    7: "np.array([x.item()], dtype=x.dtype)",
    8: "np.reshape(x, (1,) + x.shape)",
    9: "np.reshape(x, x.shape + (1,))",
    10: "np.reshape(x, (x.shape[0], 1, x.shape[1]))",
    11: "np.reshape(x, (1, x.size, 1))",
    12: "np.reshape(x, tuple(size for size in x.shape if size != 1))",
    13: "np.take(x, 0, axis=0)",
    14: "np.take(x, 0, axis=-1)",
    15: "np.stack([image.ravel(order='C') for image in x])",
    16: "np.reshape(x, (len(x), height, width))",
    17: "np.reshape(x, (len(x), x.shape[1] * x.shape[2], x.shape[3]))",
    18: "np.empty((0, x.shape[1] * x.shape[2]), dtype=x.dtype)",
}


def compile_reshaping(concept, seed):
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
            tests.append({
                "setup": setup, "args": ", ".join(inputs),
                **pack_expected(eval(ORACLES[number], env), preserve_scalar_array=True),
            })
        required = []
        if number <= 7:
            required.append("call:reshape")
        if number in (2, 3):
            required.append("literal:-1")
        if number in (8, 9, 10):
            required.append("call:expand_dims")
        if number == 11:
            required.append("attr:newaxis")
        if number in (12, 13, 14):
            required.append("call:squeeze")
        if number == 18:
            required.extend(["attr:shape", "not:literal:-1"])
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
            "required_ast": "all:" + json.dumps(required),
            "check_dtype": False, "protect_inputs": False,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "reshaping-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": inputs, "globals": ["np"],
                "allow_input_mutation": True, "result_type": "array",
            },
        }
