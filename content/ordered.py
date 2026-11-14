"""Shared compiler for authored 18-problem drills (NP09 and the pandas,
scikit-learn and PyTorch concepts).

Each concept is a pair of files. ``content/<topic>.json`` holds the wording,
the display input, the hint and the reference solution. ``content/<topic>.py``
holds the alternate inputs, an independent oracle that computes the expected
value for every fixture, the grading rules and representative wrong answers.

The oracle runs only here, in the offline compiler. Expected values never come
from executing the reference solution, so validation checks the solution
against an independent computation.
"""

import ast
import json
from pathlib import Path

from content.runner import pack, pack_expected

GENERATOR = "ordered-fixtures-v1"
STAGES = ("guided", "partial", "independent")
PREFIX = "result = "
DEFAULT_IMPORTS = {
    "numpy": "import numpy as np",
    "pandas": "import numpy as np\nimport pandas as pd",
    "sklearn": "import numpy as np",
    "pytorch": "import torch\nfrom torch import nn",
}
PACKAGES = {
    "numpy": ["numpy"],
    "pandas": ["numpy", "pandas"],
    "sklearn": ["numpy", "scikit-learn"],
    "pytorch": ["torch"],
}


def load_lessons(module_file):
    return json.loads(Path(module_file).with_suffix(".json").read_text(encoding="utf-8"))


def assigned_names(source):
    names = []
    for node in ast.parse(source).body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        for target in targets:
            for item in ast.walk(target):
                if isinstance(item, ast.Name) and item.id not in names:
                    names.append(item.id)
    return names


def imported_names(source):
    names = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.extend(alias.asname or alias.name.split(".")[0] for alias in node.names)
    return names


def packable(value):
    try:
        pack(value)
    except (TypeError, AttributeError):  # e.g. an nn.Module or an optimizer
        return False
    return True


def result_type(value):
    import numpy as np

    if isinstance(value, np.ndarray):
        return "array"
    if isinstance(value, bool) or isinstance(value, np.bool_):
        return None
    for kind, types in (("tuple", tuple), ("list", list), ("dict", dict), ("str", str)):
        if isinstance(value, types):
            return kind
    if isinstance(value, (int, float, np.integer, np.floating)):
        return "number"
    return None


def imports_for(lesson, module):
    return lesson.get("imports", DEFAULT_IMPORTS[module])


def fixtures(lesson, alternatives, seed):
    """Display input first. Seed 99 shows the same first case, then reverses."""
    return [lesson["input"], *alternatives[lesson["number"]][:: (-1 if seed == 99 else 1)]]


def evaluate(imports, fixture, oracle):
    env = {}
    exec(imports + "\n\n" + fixture, env)
    exec(oracle, env)
    return env["expected"]


def bindings(lesson, module):
    imports = imports_for(lesson, module)
    env = {}
    exec(imports + "\n\n" + lesson["input"], env)
    names = assigned_names(lesson["input"])
    inputs = [name for name in names if packable(env[name])]
    others = [name for name in names if name not in inputs]
    return imports, inputs, imported_names(imports) + others


def compile_ordered(concept, seed, concept_id, lessons, alternatives, oracles, rules):
    module = concept["module_id"]
    assert len(lessons) == 18 and [x["number"] for x in lessons] == list(range(1, 19)), concept_id
    for lesson in lessons:
        number = lesson["number"]
        pid, version, stage = lesson["id"], lesson["version"], lesson["stage"]
        rule = rules.get(number, {})
        imports, inputs, globals_ = bindings(lesson, module)
        tests = []
        kind = None
        for fixture in fixtures(lesson, alternatives, seed):
            value = evaluate(imports, fixture, oracles[number])
            kind = kind or result_type(value)
            case = {
                "setup": imports + "\n\n" + fixture,
                "args": ", ".join(inputs),
                **pack_expected(value, preserve_scalar_array=kind == "array"),
            }
            if rule.get("comparison"):
                case["comparison"] = rule["comparison"]
            tests.append(case)
        provided = imports + "\n\n" + lesson["input"] + "\n\n# 以下に答えを記入"
        body = ast.parse(lesson["solution"]).body
        single = len(body) == 1 and lesson["solution"].startswith(PREFIX)
        starter = PREFIX if single else ""
        execution = {
            "mode": "script",
            "inputs": inputs,
            "globals": globals_,
            "allow_input_mutation": not rule.get("protect_inputs", False),
        }
        if kind:
            execution["result_type"] = kind
        for flag in ("strict_division", "strict_overflow"):
            if rule.get(flag):
                execution[flag] = True
        yield {
            "id": pid, "family_id": pid, "version_id": f"{pid}@{version}",
            "content_version": version, "concept_id": concept_id, "module_id": module,
            "stage": stage, "type": "implementation", "difficulty": STAGES.index(stage) + 1,
            "title": lesson["title"], "description": lesson["task"],
            "learning_goal": concept["description"], "input_conditions": "",
            "output_conditions": lesson["task"], "starter_code": starter, "example": provided,
            "editable_regions": [{"start": len(starter), "end": len(starter)}],
            "hints": [lesson["hint"]], "solution": lesson["solution"],
            "explanation": lesson["hint"], "common_mistakes": [],
            "public_tests": tests[:2], "hidden_tests": tests[2:],
            "required_ast": rule.get("required", ""),
            "check_dtype": rule.get("dtype", module == "pytorch"),
            "protect_inputs": rule.get("protect_inputs", False),
            "runtime": "sandbox" if module == "pytorch" else "browser",
            "packages": PACKAGES[module],
            "prerequisites": concept["prerequisites"], "estimated_minutes": STAGES.index(stage) + 2,
            "variant_seed": seed, "variant_generator": GENERATOR, "tolerance": 1e-5,
            "workspace": {
                "mode": "script", "provided_code": provided, "task": lesson["task"],
                "structure": "script", "authored": True, "hint_count": 1,
            },
            "execution": execution,
        }
