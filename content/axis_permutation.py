"""Compile the authored NP04 axis permutations using an independent index oracle."""

import ast
import json
from pathlib import Path

import numpy as np

from content.runner import pack_expected

CONCEPT_ID = "NP04"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

ALTERNATIVES = {
    1: ["x = (np.arange(8) - 3).reshape(4, 2)", "x = np.array([[9, -1, 2, 8]])"],
    2: ["x = (np.arange(30) - 7).reshape(2, 3, 5)", "x = np.arange(24, 48).reshape(4, 3, 2)"],
    3: ["x = (np.arange(30) - 7).reshape(2, 3, 5)", "x = np.arange(24, 48).reshape(4, 2, 3)"],
    4: ["x = (np.arange(24) - 5).reshape(3, 4, 2)\naxes = (2, 1, 0)",
        "x = np.arange(24, 48).reshape(4, 2, 3)\naxes = (0, 2, 1)"],
    5: ["x = (np.arange(30) - 7).reshape(2, 3, 5)", "x = np.arange(24, 48).reshape(4, 2, 3)"],
    6: ["x = (np.arange(120) - 9).reshape(2, 3, 4, 5)", "x = np.arange(24, 48).reshape(3, 1, 2, 4)"],
    7: ["x = (np.arange(30) - 7).reshape(3, 5, 2)", "x = np.arange(24, 48).reshape(2, 3, 4)"],
    8: ["x = (np.arange(30) - 7).reshape(2, 3, 5)", "x = np.arange(24, 48).reshape(4, 2, 3)"],
    9: ["x = (np.arange(120) - 9).reshape(3, 2, 5, 4)", "x = np.arange(24, 48).reshape(1, 3, 4, 2)"],
    10: ["x = (np.arange(120) - 9).reshape(3, 4, 2, 5)", "x = np.arange(24, 48).reshape(1, 2, 3, 4)"],
    11: ["x = (np.arange(120) - 9).reshape(2, 3, 5, 4)", "x = np.arange(24, 48).reshape(1, 4, 3, 2)"],
    12: ["x = (np.arange(30) - 7).reshape(2, 3, 5)", "x = np.arange(24, 48).reshape(4, 2, 3)"],
    13: ["x = (np.arange(30) - 7).reshape(2, 3, 5)", "x = np.arange(24, 48).reshape(4, 2, 3)"],
    14: ["x = (np.arange(120) - 9).reshape(2, 1, 3, 4, 5)",
         "x = np.arange(120, 240).reshape(3, 2, 1, 5, 4)"],
    15: ["x = (np.arange(120) - 9).reshape(2, 1, 3, 4, 5)",
         "x = np.arange(120, 240).reshape(3, 2, 1, 5, 4)"],
    16: ["y = (np.arange(30) - 7).reshape(2, 3, 5).transpose(2, 0, 1)",
         "y = np.arange(24, 48).reshape(4, 2, 3).transpose(2, 0, 1)"],
    17: ["x = (np.arange(24) - 5).reshape(4, 2, 3)", "x = np.arange(6, 12).reshape(2, 3, 1)"],
    18: ["x = np.zeros((0, 3, 5, 2), dtype=np.float32)", "x = np.zeros((0, 1, 3, 4), dtype=np.float64)"],
}
AXES = {
    1: (1, 0), 2: (2, 1, 0), 3: (2, 0, 1), 5: (1, 0, 2),
    6: (0, 1, 3, 2), 7: (2, 0, 1), 8: (1, 2, 0),
    9: (0, 3, 1, 2), 10: (0, 2, 3, 1), 11: (0, 2, 1, 3),
    12: (1, 0, 2), 13: (1, 2, 0), 14: (0, 4, 1, 2, 3),
    15: (1, 0, 4, 2, 3), 16: (1, 2, 0), 18: (0, 3, 1, 2),
}


def expected_permutation(value, axes):
    """Map output coordinates to input coordinates without transpose APIs."""
    output = np.empty(tuple(value.shape[axis] for axis in axes), dtype=value.dtype)
    for destination in np.ndindex(output.shape):
        source = [0] * value.ndim
        for position, axis in enumerate(axes):
            source[axis] = destination[position]
        output[destination] = value[tuple(source)]
    return output


def compile_axis_permutation(concept, seed):
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
            value = env["y"] if number == 16 else env["x"]
            if number == 17:
                expected = np.stack([
                    value[:, row, col]
                    for row in range(value.shape[1]) for col in range(value.shape[2])
                ])
            else:
                axes = env["axes"] if number == 4 else AXES[number]
                expected = expected_permutation(value, axes)
            tests.append({"setup": setup, "args": ", ".join(inputs), **pack_expected(expected)})
        if number in (1, 2):
            required = ["attr:T"]
        elif number in (5, 6, 11, 12):
            required = ["call:swapaxes"]
        elif number in (7, 8):
            required = ["call:moveaxis"]
        elif number == 15:
            required = ["call-count:moveaxis:1"]
        elif number == 17:
            required = ["call:reshape"]
        else:
            required = ["call:transpose"]
        if number == 6:
            required.extend(["literal:-1", "literal:-2"])
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
            "variant_seed": seed, "variant_generator": "axis-permutation-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": inputs, "globals": ["np"],
                "allow_input_mutation": True, "result_type": "array",
            },
        }
