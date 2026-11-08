"""Compile the authored NP01 array, shape and dtype practice in display order."""

import ast
import json
from pathlib import Path

from content.runner import pack_expected

CONCEPT_ID = "NP01"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

# Each exercise has one additional public input and one private input. Fixed
# conditions such as a 2x3 input, scalar array or (0, 4) shape remain fixed.
ALTERNATIVES = {
    1: ["values = [0, 2, -4]", "values = []"],
    2: ["values = [[-1, 0, 8], [3, -5, 2]]", "values = [[0.5, -1.5, 2.5], [3.5, 4.5, 0.0]]"],
    3: ["values = [-2, 0, 5]", "values = [0.25, -1.75]"],
    4: ["x = np.array([[1], [2], [3]])", "x = np.zeros((0, 4))"],
    5: ["x = np.zeros((3, 2))", "x = np.zeros((1, 2, 1, 3))"],
    6: ["x = np.ones((2, 3, 4))", "x = np.zeros((0, 2))"],
    7: ["x = np.zeros((0, 3))", "x = np.array([[9, 1, 2, 3]])"],
    8: ["x = np.array([2, 4], dtype=np.int32)", "x = np.array([0.25], dtype=np.float64)"],
    9: ["rows = 0\ncols = 4", "rows = 3\ncols = 1"],
    10: ["shape = (1, 4)", "shape = (0, 2, 3)"],
    11: ["shape = (3,)\ninitial_value = 0.25", "shape = (1, 2, 2)\ninitial_value = 2.5"],
    12: ["stop = 0\nstep = 2", "stop = 8\nstep = 2"],
    13: ["start = -1.0\nstop = 2.0\nnum = 4", "start = 2.0\nstop = 5.0\nnum = 2"],
    14: ["x = np.array([[0.5, -2.0]], dtype=np.float32)", "x = np.array([True, False], dtype=np.bool_)"],
    15: ["x = np.array([-7, 0, 12], dtype=np.int16)", "x = np.zeros((0, 3), dtype=np.int64)"],
    16: ["x = np.array([-3.9, 3.9, -0.9, 0.9], dtype=np.float32)",
         "x = np.array([[-1.2, 1.2], [-0.25, 0.25]], dtype=np.float64)"],
    17: ["x = np.array(-5, dtype=np.int16)", "x = np.array(1.5, dtype=np.float64)"],
    18: ["x = np.zeros((0, 4), dtype=np.int16)", "x = np.zeros((0, 4), dtype=np.float64)"],
}

# Independent expected-value expressions, evaluated only by the trusted compiler.
ORACLES = {
    1: "np.asarray(values)",
    2: "np.asarray(values)",
    3: "np.asarray(values, dtype='float32')",
    4: "tuple(np.shape(x))",
    5: "len(x.shape)",
    6: "int(np.prod(x.shape))",
    7: "len(x)",
    8: "str(x.dtype)",
    9: "np.full((rows, cols), 0, dtype='float64')",
    10: "np.full(shape, 1, dtype='float32')",
    11: "np.ones(shape, dtype='float32') * np.float32(initial_value)",
    12: "np.asarray(list(range(0, stop, step)), dtype='int64')",
    13: "np.asarray([start + (stop - start) * i / (num - 1) for i in range(num)])",
    14: "np.full(x.shape, 0, dtype=x.dtype)",
    15: "np.asarray(x.tolist(), dtype='float64').reshape(x.shape)",
    16: "np.asarray(np.trunc(x), dtype='int32')",
    17: "((), 0, 1)",
    18: "((0, 4), 2, 0)",
}
REQUIREMENTS = {
    1: ["call:array"], 2: ["call:array"], 3: ["call:array"],
    4: ["shape"], 7: ["shape"], 8: ["attr:dtype"],
    9: ["call:zeros"], 10: ["call:ones"], 11: ["call:full"],
    12: ["call:arange"], 13: ["call:linspace"], 14: ["call:zeros_like"],
    15: ["call:astype"], 16: ["call:astype"],
    17: ["attr:shape", "attr:ndim", "attr:size"],
    18: ["attr:shape", "attr:ndim", "attr:size"],
}


def compile_arrays(concept, seed):
    for lesson in LESSONS:
        number = lesson["number"]
        pid, version, stage = lesson["id"], lesson["version"], lesson["stage"]
        inputs = [target.id for node in ast.parse(lesson["input"]).body
                  for target in node.targets if isinstance(target, ast.Name)]
        fixtures = [lesson["input"], *ALTERNATIVES[number][::(-1 if seed == 99 else 1)]]
        tests = []
        for fixture in fixtures:
            setup = "import numpy as np\n\n" + fixture
            env = {}
            exec(setup, env)
            tests.append({
                "setup": setup, "args": ", ".join(inputs),
                **pack_expected(eval(ORACLES[number], env)),
            })
        execution = {
            "mode": "script", "inputs": inputs, "globals": ["np"],
            "allow_input_mutation": False,
        }
        if number in (4, 17, 18):
            execution["result_type"] = "tuple"
        if number == 8:
            execution["result_type"] = "str"
        if number in (17, 18):
            execution["constant_goal"] = True
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
            "required_ast": "all:" + json.dumps(REQUIREMENTS.get(number, [])),
            "check_dtype": number not in (1, 2, 13), "protect_inputs": True,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "array-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": execution,
        }
