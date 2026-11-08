"""Compile the authored, ordered PY01 expression practice."""
import ast
import json
from pathlib import Path
from content.runner import pack_expected

CONCEPT_ID = "PY01"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "
# Two independently specified alternatives per exercise. The empty input is
# covered in both variants, with one nonempty alternative public and one private.
ALTERNATIVES = {
    1: [(([0, 7, -2, 7],), [0, 14, -4, 14]), (([-5],), [-10])],
    7: [(([255, 1, 32],), [1.0, 1 / 255, 32 / 255]), (([42, 200],), [42 / 255, 200 / 255])],
    8: [(([3, -4, -4, 0],), [9, 16, 16, 0]), (([-1, 10],), [1, 100])],
    2: [(([0, 3, -8, 3],), [3, 3]), (([-2, 0, -4],), [])],
    9: [(([-6, -3, 1, 10, 0],), [-6, 10, 0]), (([7, -5],), [])],
    10: [(([0.7, 0.69, 1.0, 0.7],), [0.7, 1.0, 0.7]), (([0.01, 0.699],), [])],
    3: [(([0.5, 0.49, 1.0, 0.0, 0.5],), [0, 2, 4]), (([0.2, 0.49],), [])],
    11: [(([-4, 0, -3, 2],), [0, 0, -6, 6]), (([12],), [0])],
    12: [(([-3, 0, 7, 12],), [-2, 2, 10, 16]), (([0],), [1])],
    4: [(([-2, 0, 3, 5], [2, -1, 0.5]), [-4, 0, 1.5]), (([7], [0, 1]), [0])],
    13: [(([-2, 3], [2, 0, 5]), [0, 3]), (([7, 0, 2, 1], [-3, -1, 2, 4]), [4, -1, 4, 5])],
    14: [(([-1, 4, 8, 0], [3, 4, 3]), [4, 0, 5]), (([7, 0], [2, 9]), [5, 9])],
    5: [((["plane", "truck", "plane"],), {"plane": 2, "truck": 1}), ((["horse"],), {"horse": 0})],
    15: [((["first", "second", "first"], [1, 2, 3]), {"first": 3, "second": 2}),
         ((["a", "b", "c"], [0.25, 0.5]), {"a": 0.25, "b": 0.5})],
    16: [(({"a": -1, "b": 0, "c": 3, "d": 1},), {"c": 3, "d": 1}), (({"a": -2, "b": 0},), {})],
    6: [(([[], [7], [-1, 0, 4], []],), [7, -1, 0, 4]), (([[], []],), [])],
    17: [(([[], [-2, 0], [3], []],), [-4, 0, 6]), (([[], []],), [])],
    18: [(([0.2, 0.05, 0.001], [8]), [[0.2, 8], [0.05, 8], [0.001, 8]]),
         (([0.03], [4, 16, 64]), [[0.03, 4], [0.03, 16], [0.03, 64]])],
}

def compile_iteration(concept, seed):
    for lesson in LESSONS:
        number = lesson["number"]
        pid = f"{CONCEPT_ID}-{number:02}"
        version = lesson["version"]
        stage = lesson["stage"]
        provided, assignment = lesson["starter"].rsplit("\n", 1)
        assert assignment == PREFIX.rstrip()
        inputs = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in ast.parse(provided).body
        }
        examples = ALTERNATIVES[number][::(-1 if seed == 99 else 1)]
        empty = tuple(type(value)() for value in inputs.values())
        expected_empty = type(lesson["expected"])()
        cases = [
            (tuple(inputs.values()), lesson["expected"]),
            examples[0],
            (empty, expected_empty),
            examples[1],
        ]
        tests = []
        for args, expected in cases:
            # JSON cannot express tuples. This authored result-type contract,
            # rather than the shape of the values, defines the pair elements.
            if lesson["result_type"] == "list_of_pairs":
                expected = [tuple(pair) for pair in expected]
            tests.append({"setup": "", "args": repr(args)[1:-1], **pack_expected(expected)})
        yield {
            "id": pid, "family_id": pid, "version_id": f"{pid}@{version}",
            "content_version": version, "concept_id": CONCEPT_ID, "module_id": "python",
            "stage": stage,
            "type": "implementation", "difficulty": ("guided", "partial", "independent").index(stage) + 1,
            "title": lesson["title"], "description": lesson["task"],
            "learning_goal": concept["description"], "input_conditions": "",
            "output_conditions": lesson["task"], "starter_code": PREFIX, "example": provided,
            "editable_regions": [{"start": len(PREFIX), "end": len(PREFIX)}],
            "hints": [lesson["hint"]], "solution": lesson["solution"],
            "explanation": lesson["hint"], "common_mistakes": [],
            "public_tests": tests[:2], "hidden_tests": tests[2:],
            "required_ast": f"comprehension:{lesson['requirement']}", "check_dtype": True,
            "protect_inputs": True, "runtime": "browser", "packages": [],
            "prerequisites": concept["prerequisites"], "estimated_minutes": 2,
            "variant_seed": seed, "variant_generator": "iteration-fixtures-v1", "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": {
                "mode": "script", "inputs": list(inputs), "globals": [],
                "allow_input_mutation": False,
                "result_type": lesson["result_type"],
            },
        }
