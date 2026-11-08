"""Compile the authored NP05 reductions with independent, small input oracles."""

import json
import statistics
from pathlib import Path

import numpy as np

from content.runner import pack_expected

CONCEPT_ID = "NP05"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

MATRICES = [
    "x = np.array([[-2, 4], [7, 1], [3, -5]])",
    "x = np.array([[9, -3, 0, 2]])",
]
FLOAT_MATRICES = [
    "x = np.array([[-2.5, 4.0], [7.5, 1.0], [3.0, -5.0]])",
    "x = np.array([[9.5, -3.0, 0.0, 2.5]])",
]
IMAGE_BATCHES = [
    "x = (np.arange(12, dtype=np.float64) - 5).reshape(1, 3, 4)",
    "x = np.array([[[2.0, 8.0]], [[-4.0, 0.0]], [[1.0, 6.0]]])",
]
CHANNEL_BATCHES = [
    "x = (np.arange(24, dtype=np.float64) - 7).reshape(1, 3, 2, 4)",
    "x = (np.arange(12, dtype=np.float64) * 0.5 - 2).reshape(2, 1, 3, 2)",
]
ALTERNATIVES = {
    **{number: MATRICES for number in (1, 3, 4, 7, 8, 11, 12)},
    **{number: FLOAT_MATRICES for number in (2, 5, 6, 10, 13)},
    9: ["x = np.array([[4, 4], [9, 1], [-2, -2]])",
        "x = np.array([[6, 1, 6, 0]])"],
    14: IMAGE_BATCHES,
    15: CHANNEL_BATCHES,
    16: CHANNEL_BATCHES,
    17: ["x = np.array([[-2.5, 4.0], [7.5, 1.0], [3.0, -5.0]], dtype=np.float32)",
         "x = np.array([[9.5, -3.0, 0.0, 2.5]], dtype=np.float64)"],
    18: ["x = np.zeros((0, 5), dtype=np.float32)",
         "x = np.zeros((0, 1), dtype=np.float64)"],
}


def expected_reduction(number, x):
    """Compute expectations using Python row/column traversal, not model code."""
    rows = x.tolist()
    if number in (14, 15, 16):
        if number == 14:
            return np.array([statistics.mean(v for row in image for v in row)
                             for image in rows])
        means = np.array([[statistics.mean(v for row in channel for v in row)
                           for channel in image] for image in rows])
        return means.reshape(x.shape[:2] + (1, 1)) if number == 16 else means
    columns = [[row[col] for row in rows] for col in range(x.shape[1])]
    flat = [v for row in rows for v in row]
    if number == 1:
        return sum(flat)
    if number == 2:
        return statistics.mean(flat)
    if number == 3:
        return np.array([sum(row) for row in rows])
    if number in (4, 11, 18):
        totals = [sum(col) for col in columns]
        return np.array([totals] if number == 11 else totals)
    if number == 5:
        return np.array([statistics.mean(row) for row in rows])
    if number == 6:
        return np.array([statistics.mean(col) for col in columns])
    if number in (7, 12):
        maxima = [max(row) for row in rows]
        return np.array([[v] for v in maxima] if number == 12 else maxima)
    if number == 8:
        return np.array([min(col) for col in columns])
    if number == 9:
        return np.array([row.index(max(row)) for row in rows])
    if number == 10:
        return np.array([statistics.pstdev(col) for col in columns])
    if number == 13:
        return np.array([[statistics.mean(flat)]])
    if number == 17:
        average = statistics.mean(flat)
        return np.array([[v - average for v in row] for row in rows])
    raise ValueError(number)


def compile_reductions(concept, seed):
    for lesson in LESSONS:
        number = lesson["number"]
        pid, version, stage = lesson["id"], lesson["version"], lesson["stage"]
        tests = []
        for fixture in [lesson["input"], *ALTERNATIVES[number][::(-1 if seed == 99 else 1)]]:
            setup = "import numpy as np\n\n" + fixture
            env = {}
            exec(setup, env)
            tests.append({"setup": setup, "args": "x",
                          **pack_expected(expected_reduction(number, env["x"]))})
        api = {1: "sum", 2: "mean", 9: "argmax", 10: "std", 11: "sum",
               12: "max", 13: "mean", 18: "sum"}.get(number)
        required = [f"call:{api}"] if api else []
        if number in (10, 11, 12, 13, 16):
            required.append("call-keywords:" + json.dumps({
                "name": api,
                "keywords": {"ddof": 0} if number == 10 else {"keepdims": True},
            }))
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
            "check_dtype": False, "protect_inputs": number == 17,
            "runtime": "browser", "packages": ["numpy"],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "reduction-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": ["x"], "globals": ["np"],
                "allow_input_mutation": True,
                "result_type": "number" if number in (1, 2) else "array",
            },
        }
