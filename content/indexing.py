"""Compile the authored NP02 indexing exercises in their specified order."""

import ast
import json
from pathlib import Path

from content.runner import pack_expected

CONCEPT_ID = "NP02"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

ALTERNATIVES = {
    1: ["x = np.array([-2, 0, 7, 4])\nindex = 0", "x = np.array([9])\nindex = 0"],
    2: ["x = np.array([-4, 3, 0])", "x = np.array([7])"],
    3: ["x = np.array([-3, 0, 7, 4])\nstart = 0\nstop = 2",
        "x = np.array([1, 2, 3])\nstart = 2\nstop = 2"],
    4: ["x = np.array([-2, 0, 3])", "x = np.array([], dtype=np.int64)"],
    5: ["x = np.array([[2, 4, 6, 8], [1, 3, 5, 7]])\nrow = 0\ncol = 3",
        "x = np.array([[9, -1]])\nrow = 0\ncol = 0"],
    6: ["x = np.array([[-2, 0], [3, 7]])\nrow = 0",
        "x = np.array([[9, 1, 2, 3]])\nrow = 0"],
    7: ["x = np.array([[1, 4], [2, 5], [3, 6], [0, 7]])\ncol = 0",
        "x = np.zeros((0, 3), dtype=np.int64)\ncol = 2"],
    8: ["x = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])\ncol = 3",
        "x = np.zeros((0, 2), dtype=np.int64)\ncol = 0"],
    9: ["x = np.array([[1, 2], [3, 4], [5, 6]])\nrow_start = 0\nrow_stop = 2\ncol_start = 0\ncol_stop = 1",
        "x = np.array([[1, 2, 3], [4, 5, 6]])\nrow_start = 1\nrow_stop = 1\ncol_start = 1\ncol_stop = 3"],
    10: ["x = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])", "x = np.array([[9, 0, -1]])"],
    11: ["x = np.arange(12).reshape(3, 4)\ncolumns = [3, 1, 3, 0]",
         "x = np.array([[1, 2, 3], [4, 5, 6]])\ncolumns = []"],
    12: ["x = np.array([-1, 0, 1, 0])\nthreshold = 0",
         "x = np.array([], dtype=np.int64)\nthreshold = 3"],
    13: ["x = np.array([-4, -2, -2, 0, 3])\nthreshold = -2",
         "x = np.array([1, 2, 3])\nthreshold = 4"],
    14: ["x = np.array([-2, 0, 1, 2, 3])\nlower = 0\nupper = 2",
         "x = np.array([-1, 0, 1])\nlower = 2\nupper = 3"],
    15: ["x = np.array([-2, 0, 1, 2, 4])\nlower = 0\nupper = 2",
         "x = np.array([0, 1, 2])\nlower = 0\nupper = 2"],
    16: ["x = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])\nlabels = np.array([2, 1, 2])\ntarget = 2",
         "x = np.array([[1, 2, 3], [4, 5, 6]])\nlabels = np.array([0, 0])\ntarget = 1"],
    17: ["x = np.array([np.nan, np.nan])", "x = np.array([np.inf, np.nan, -np.inf, 0.0])"],
    18: ["x = np.array([[7, 0, 9], [2, 7, 8]])\nthreshold = 7",
         "x = np.zeros((3, 2), dtype=np.int64)\nthreshold = 1"],
}

# Expected values are computed independently of the reference answer.
ORACLES = {
    1: "np.take(x, index)",
    2: "x.item(len(x) - 1)",
    3: "np.take(x, np.arange(start, stop))",
    4: "np.take(x, np.arange(len(x) - 1, -1, -1))",
    5: "np.take(x, row * x.shape[1] + col)",
    6: "np.take(x, row, axis=0)",
    7: "np.take(x, col, axis=1)",
    8: "np.take(x, [col], axis=1)",
    9: "np.take(np.take(x, np.arange(row_start, row_stop), axis=0), np.arange(col_start, col_stop), axis=1)",
    10: "np.take(x, np.arange(0, len(x), 2), axis=0)",
    11: "np.take(x, columns, axis=1)",
    12: "np.greater_equal(x, threshold)",
    13: "np.asarray([value for value in x if value >= threshold], dtype=x.dtype)",
    14: "np.asarray([value for value in x if lower <= value < upper], dtype=x.dtype)",
    15: "np.asarray([value for value in x if value < lower or value > upper], dtype=x.dtype)",
    16: "np.take(x, [i for i, label in enumerate(labels) if label == target], axis=0)",
    17: "np.asarray([value for value in x if not np.isnan(value)], dtype=x.dtype)",
    18: "np.asarray([value for row in x for value in row if value >= threshold], dtype=x.dtype)",
}


def compile_indexing(concept, seed):
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
                **pack_expected(eval(ORACLES[number], env)),
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
            "required_ast": {2: "USub", 3: "Slice", 4: "Slice"}.get(number, ""),
            "check_dtype": number == 12, "protect_inputs": True,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "indexing-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": inputs, "globals": ["np"],
                "allow_input_mutation": False,
            },
        }
