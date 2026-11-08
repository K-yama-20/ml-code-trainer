"""Compile the authored NP06 practice with coordinate-by-coordinate oracles."""

import ast
import json
from pathlib import Path

import numpy as np

from content.runner import pack_expected

CONCEPT_ID = "NP06"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

MATRIX = ["x = np.array([[-2, 8], [1, 5], [9, -4]])",
          "x = np.array([[7, 2, -3, 10]])"]
ALTERNATIVES = {
    1: [MATRIX[0] + "\noffset = -4", MATRIX[1] + "\noffset = 0.5"],
    2: ["pixels = np.array([[0, 255], [32, 96], [160, 240]], dtype=np.float64)",
        "pixels = np.array([[16, 64, 128, 0]], dtype=np.float64)"],
    3: [MATRIX[0] + "\nbias = np.array([-7, 2])",
        MATRIX[1] + "\nbias = np.array([0.5, -3, 6, 1])"],
    4: [MATRIX[0] + "\nweights = np.array([-2.0, 0.25])",
        MATRIX[1] + "\nweights = np.array([0.5, -1, 2, 0])"],
    5: [MATRIX[0] + "\nbias = np.array([9, -1, 3])",
        MATRIX[1] + "\nbias = np.array([0.5])"],
    6: [MATRIX[0] + "\nweights = np.array([-2.0, 0.25, 3.0])",
        MATRIX[1] + "\nweights = np.array([4.0])"],
    7: ["row_values = np.array([[-2], [7], [4]])\ncol_values = np.array([[3, -1]])",
        "row_values = np.array([[5]])\ncol_values = np.array([[0, 2, -4, 9]])"],
    8: ["a = np.array([-2, 7, 4])\nb = np.array([3, -1])",
        "a = np.array([5])\nb = np.array([0, 2, -4, 9])"],
    9: ["a = np.array([-2, 7, 4])\nb = np.array([3, -1])",
        "a = np.array([5])\nb = np.array([0, 2, -4, 9])"],
    10: MATRIX,
    11: MATRIX,
    12: ["x = np.array([[0.0, 2.0], [3.0, 1.0], [2.0, 6.0]])",
         "x = np.array([[2.0, 0.0, 1.0, 5.0]])"],
    13: [MATRIX[0] + "\nmeans = np.array([1.0, -2.0])\nstds = np.array([0.5, 4.0])",
         MATRIX[1] + "\nmeans = np.array([-1.0, 2.0, 0.0, 4.0])\nstds = np.array([2.0, 0.5, 4.0, 5.0])"],
    14: ["image = (np.arange(24, dtype=np.float64) - 5).reshape(3, 2, 4)\nbias = np.array([0.5, -2, 7, 3])",
         "image = np.arange(8, dtype=np.float64).reshape(1, 4, 2)\nbias = np.array([-1.0, 4.0])"],
    15: ["x = (np.arange(24, dtype=np.float64) - 5).reshape(1, 2, 3, 4)\nbias = np.array([-2.0, 7.0])",
         "x = np.arange(24, dtype=np.float64).reshape(3, 4, 2, 1)\nbias = np.array([0.5, -3, 6, 1])"],
    16: ["x = (np.arange(24, dtype=np.float64) - 5).reshape(3, 2, 1, 4)\nweights = np.array([-2.0, 0.25, 3.0])",
         "x = np.arange(24, dtype=np.float64).reshape(1, 3, 4, 2)\nweights = np.array([4.0])"],
    17: ["values = np.array([-2, 7])\nrows = 3", "values = np.array([0.5, -1, 4, 2])\nrows = 1"],
    18: ["points = np.array([[1.0, -2.0, 3.0], [4.0, 0.0, -1.0]])\ncenters = np.array([[0.0, 1.0, 2.0], [-1.0, 3.0, 0.0], [2.0, -2.0, 1.0], [5.0, 1.0, -3.0]])",
         "points = np.array([[1.0, -2.0, 3.0, 4.0]])\ncenters = np.array([[0.0, 1.0, 2.0, -1.0], [3.0, -2.0, 0.0, 5.0], [-1.0, 4.0, 2.0, 0.0]])"],
}


def expected_broadcast(number, env):
    """Apply each specification to individual coordinates, without broadcasting."""
    if number in (7, 8, 9, 17, 18):
        if number == 7:
            shape = (len(env["row_values"]), env["col_values"].shape[1])
            element = lambda i: env["row_values"][i[0], 0] + env["col_values"][0, i[1]]
        elif number in (8, 9):
            shape = (len(env["a"]), len(env["b"]))
            element = (lambda i: env["a"][i[0]] * env["b"][i[1]]) if number == 8 else (
                lambda i: env["a"][i[0]] - env["b"][i[1]])
        elif number == 17:
            shape = (env["rows"], len(env["values"]))
            element = lambda i: env["values"][i[1]]
        else:
            points, centers = env["points"], env["centers"]
            shape = (len(points), len(centers))
            element = lambda i: sum((points[i[0], k] - centers[i[1], k]) ** 2
                                    for k in range(points.shape[1]))
    else:
        x = env["pixels"] if number == 2 else env["image"] if number == 14 else env["x"]
        shape = x.shape
        if number == 1:
            element = lambda i: x[i] + env["offset"]
        elif number == 2:
            element = lambda i: x[i] / 255
        elif number in (3, 5, 14, 15):
            axis = {3: 1, 5: 0, 14: 2, 15: 1}[number]
            element = lambda i: x[i] + env["bias"][i[axis]]
        elif number in (4, 6, 16):
            axis = 1 if number == 4 else 0
            element = lambda i: x[i] * env["weights"][i[axis]]
        elif number == 10:
            means = [sum(float(x[r, c]) for r in range(x.shape[0])) / x.shape[0]
                     for c in range(x.shape[1])]
            element = lambda i: x[i] - means[i[1]]
        elif number in (11, 12):
            totals = [sum(float(v) for v in row) for row in x]
            element = (lambda i: x[i] - totals[i[0]] / x.shape[1]) if number == 11 else (
                lambda i: x[i] / totals[i[0]])
        elif number == 13:
            element = lambda i: (x[i] - env["means"][i[1]]) / env["stds"][i[1]]
        else:
            raise ValueError(number)
    return np.array([element(index) for index in np.ndindex(shape)]).reshape(shape)


def compile_broadcasting(concept, seed):
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
            tests.append({"setup": setup, "args": ", ".join(inputs),
                          **pack_expected(expected_broadcast(number, env))})
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
            "required_ast": "call:broadcast_to" if number == 17 else "",
            "check_dtype": False, "protect_inputs": True,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "broadcasting-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": inputs, "globals": ["np"],
                "allow_input_mutation": False, "result_type": "array",
            },
        }
