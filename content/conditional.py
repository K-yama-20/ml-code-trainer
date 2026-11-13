"""Compile NP08 with authored examples and element-by-element expectations."""

import ast
import json
import math
from pathlib import Path

import numpy as np

from content.runner import pack_expected

CONCEPT_ID = "NP08"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

PREDICTION_PAIRS = [
    "pred = np.array([[2., 1.], [-3., 0.], [5., 2.]])\ntarget = np.array([[0., 4.], [-3., 3.], [1., 2.]])",
    "pred = np.array([[0.5, -1., 3., 4.]])\ntarget = np.array([[1., -2., 0., 4.]])",
]
ALTERNATIVES = {
    1: ["x = np.array([[-1.5, 0, 4], [-2, 9, -7]])", "x = np.array([3.5, -1., 0.])"],
    2: ["a = np.array([[2, 0], [5, 3], [-1, 8]])\nb = -a - 10\nuse_a = np.array([[False, True], [True, True], [False, False]])",
        "a = np.array([[2.5, 3, 8, -1]])\nb = np.array([[0, -5, 4, 7]])\nuse_a = np.array([[False, True, False, True]])"],
    3: ["x = np.array([[-4, -2, 0], [5, -2, -3]])\nthreshold = -2",
        "x = np.array([2.25, 4.5, 4.75])\nthreshold = 4.5"],
    4: ["x = np.array([[-5, -3, 0], [1, 2, 9]])\nlower = -3\nupper = 2\nfallback = 14",
        "x = np.array([6, 7, 8])\nlower = 7\nupper = 7\nfallback = -2"],
    5: ["scores = np.array([[-5, -4, 0], [3, 4, 7]])\nlower = -4\nupper = 3",
        "scores = np.array([0.2, 0.25, 0.5, 0.75])\nlower = 0.25\nupper = 0.75"],
    6: ["a = np.array([[-3, 8], [0, 2], [4, 5]])\nb = np.array([[0, 2], [5, 2], [-4, 6]])",
        "a = np.array([[8, -3, 1, 0]])\nb = np.array([[1, 6, 1, 3]])"],
    7: ["requested = np.array([0, 7, 2])\navailable = np.array([3, 2, 2])",
        "requested = np.array([1, 6, 8, 4, 0])\navailable = np.array([8, 1, 8, 0, 3])"],
    8: ["x = np.array([[-4., 0., 0.1], [0.7, 1., 2.5]])", "x = np.array([0.75, 4., -2., 1.])"],
    9: ["x = np.array([[-8, -3, 0], [7, 12, -4]])\nlower = -3",
        "x = np.array([5., 5.5, 25.])\nlower = 5.5"],
    10: ["x = np.array([[-9, -6, -3], [0, 2, -12]])\nupper = -6",
         "x = np.array([-30, 25, 27])\nupper = 25"],
    11: ["x = np.array([[-2, 8], [1, 4], [9, 6]])\nlower = np.array([1, 4])\nupper = np.array([7, 6])",
         "x = np.array([[-4, 9, 14, -1]])\nlower = np.array([0, -5, 14, -6])\nupper = np.array([6, 8, 14, 2])"],
    12: ["pixels = np.array([[-300, 255], [256, 7], [0, 512]], dtype=np.int32)",
         "pixels = np.array([[-1, 31, 256, 1024]], dtype=np.int64)"],
    13: PREDICTION_PAIRS,
    14: [PREDICTION_PAIRS[0] + "\nvalid = np.array([[False, True], [True, False], [True, False]])",
         PREDICTION_PAIRS[1] + "\nvalid = np.array([[True, False, True, False]])"],
    15: ["x = np.array([[np.inf, -np.inf], [np.nan, 9.], [-7., np.nan]])",
         "x = np.array([-np.inf, 0., np.nan, np.inf])"],
    16: ["x = np.array([[np.nan, -np.inf, -12.], [np.inf, 10., 0.]])\nhigh = 3.0\nlow = -2.0",
         "x = np.array([np.inf, 6., -np.inf, -5., np.nan, np.nan])\nhigh = 1.5\nlow = -0.5"],
    17: ["x = np.array([[-2., 0., 0.1], [0.25, 1., 4.]])\neps = 0.25",
         "x = np.array([-1., 0., 0.25, 0.5, 2.])\neps = 0.5"],
    18: ["numerator = np.array([[0., 3.], [5., -8.], [6., 0.]])\ndenominator = np.array([[0., -0.0], [2., -2.], [3., 4.]])",
         "numerator = np.array([[-7., 0., 9., -6., 0.]])\ndenominator = np.array([[0., 0., 3., 2., -1.]])"],
}

REQUIRED_APIS = {
    1: "where", 2: "where", 4: "where", 5: "where", 6: "maximum", 7: "minimum",
    8: "clip", 9: "clip", 10: "clip", 11: "clip", 12: "clip", 14: "where",
    16: "nan_to_num", 17: "clip", 18: "divide",
}
RESULT_DTYPES = {3: np.int64, 12: np.uint8}


def expected_element(number, env, index):
    if number == 2:
        return env["a" if env["use_a"][index] else "b"][index]
    if number == 5:
        score = env["scores"][index]
        return 0 if score < env["lower"] else 1 if score < env["upper"] else 2
    if number == 6:
        return max(env["a"][index], env["b"][index])
    if number == 7:
        return min(env["requested"][index], env["available"][index])
    if number == 12:
        return max(0, min(255, int(env["pixels"][index])))
    if number in (13, 14):
        if number == 14 and not env["valid"][index]:
            return 0.0
        return (env["pred"][index] - env["target"][index]) ** 2
    if number == 18:
        denominator = env["denominator"][index]
        return env["numerator"][index] / denominator if denominator != 0 else 0.0

    value = env["x"][index]
    if number == 1:
        return max(0.0, value)
    if number == 3:
        return int(value >= env["threshold"])
    if number == 4:
        return value if env["lower"] <= value <= env["upper"] else env["fallback"]
    if number == 8:
        return min(1.0, max(0.0, value))
    if number == 9:
        return max(env["lower"], value)
    if number == 10:
        return min(env["upper"], value)
    if number == 11:
        column = index[1]
        return min(env["upper"][column], max(env["lower"][column], value))
    if number in (15, 16):
        if math.isnan(value):
            return 0.0
        if number == 16 and math.isinf(value):
            return env["high"] if value > 0 else env["low"]
        return value
    if number == 17:
        return math.log(max(env["eps"], value))
    raise ValueError(number)


def compile_conditional(concept, seed):
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
            shape = env[inputs[0]].shape
            values = [expected_element(number, env, index) for index in np.ndindex(shape)]
            expected = np.array(values, dtype=RESULT_DTYPES.get(number)).reshape(shape)
            tests.append({"setup": setup, "args": ", ".join(inputs), **pack_expected(expected)})
        provided = "import numpy as np\n\n" + lesson["input"] + "\n\n# 以下に答えを記入"
        execution = {
            "mode": "script", "inputs": inputs, "globals": ["np"],
            "allow_input_mutation": True, "result_type": "array",
        }
        if number == 18:
            execution["strict_division"] = True
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
            "required_ast": f"call:{REQUIRED_APIS[number]}" if number in REQUIRED_APIS else "",
            "check_dtype": number in RESULT_DTYPES, "protect_inputs": False,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "conditional-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": execution,
        }
