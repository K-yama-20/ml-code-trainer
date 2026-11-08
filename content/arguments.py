"""Compile the authored PY02 exercises without rewriting the displayed code."""

import ast
import json
from pathlib import Path

from content.runner import pack_expected

CONCEPT_ID = "PY02"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))

# The first case is the authored display. These are additional inputs and
# independently specified results, with one public and two private per seed.
CALL_CASES = {
    1: [((-5, 4, 3), -17), ((2, -3, 8), 2), ((7, 0, -6), -6)],
    2: [((-4, 2, 9), 2), ((6, -3, 11), 6), ((20, 10, 14), 14)],
    3: [((-3, 5, 2), -13), ((7, -2, 0), -14), ((8, 0, -1), -1)],
    4: [(([0, 5],), [0, 10]), (([-7],), [-14]), (([],), [])],
    5: [(([-3, 2],), [-9, 6]), (([0, 4, 1],), [0, 12, 3]), (([7],), [21])],
    6: [((25,), 0.35), ((-60,), -0.5), ((0,), 0.1)],
    13: [(([0, -10, 4],), -1.0), (([5, 0, 2],), 2.0), (([-2, 9, 0],), 2.3)],
    14: [((-2, (5, 7)), -3), ((0, (8, -6)), -6), ((3, (-4, 0)), -12)],
    15: [(([2], [4, 6, 10]), 5.5), (([4, 0, -2], [10]), 3.0), (([], [0, 4, 2, 6]), 3.0)],
    16: [
        (({"batch_size": 8, "lr": 0.02},), (0.02, 8)),
        (({"lr": 0.0, "batch_size": 16},), (0.0, 16)),
        (({"lr": 0.002, "batch_size": 128},), (0.002, 128)),
    ],
    17: [
        (([], {"epochs": 3}), (0, 0.01, 3)),
        (([1, 2], {"lr": 0.0}), (2, 0.0, 5)),
        (([7], {"epochs": 4, "lr": 0.02}), (1, 0.02, 4)),
    ],
}
FUNCTION_CASES = {
    7: [("1.25, -0.5", 0.75), ("", 0), ("-2, 0, 3, 4", 5)],
    8: [("0.75", 0.75), ("-1, 2, 0, 3", 1.0), ("0.125, 0.375", 0.25)],
    9: [("0.0, 0.0, -0.1, 2.0", 2), ("1.5", 0), ("3, 2, 3, 3, 4", 3)],
    10: [("batch_size=16", 0.001), ("lr=0.0", 0.0), ("lr=0.025, note='test'", 0.025)],
    11: [("first=False, second=False, third=True", 1), ("", 0), ("amp=True, shuffle=True, logging=True, pin=False", 3)],
    12: [("note='trial', batch_size=8", {"batch_size": 8}), ("", {}), ("epochs=4, lr=0.0", {"lr": 0.0})],
    18: [
        ("compute_error, -2, 3, absolute=True", 5),
        ("compute_error, 2, 7", -5),
        ("combine, 2, 3, 4, bias=1, scale=2", 19),
    ],
}
FUNCTION_SETUP = {
    "combine": "def combine(*values, bias=0, scale=1):\n    return sum(values) * scale + bias",
}
CALL_RULES = {
    1: {"forms": [[3, []]]},
    2: {"forms": [[0, ["x", "lower", "upper"]]]},
    3: {"forms": [[2, ["bias"]]]},
    4: {"forms": [[1, []], [0, ["values"]]]},
    5: {"forms": [[2, []], [1, ["factor"]], [0, ["values", "factor"]]]},
    6: {"forms": [[1, ["offset"]], [0, ["score", "offset"]]]},
    13: {"unpack": [0, True, False]},
    14: {"unpack": [1, True, False]},
    15: {"unpack": [0, True, False]},
    16: {"unpack": [0, False, True]},
    17: {"unpack": [1, False, True]},
}


def call_tests(number, name, provided, inputs, lesson, seed):
    cases = [(tuple(inputs.values()), lesson["expected"]), *CALL_CASES[number]]
    if seed == 99:
        cases[2:] = reversed(cases[2:])
    for values, expected in cases:
        setup = provided
        if number in (1, 3, 15):
            # The arithmetic alone cannot distinguish permutations here.
            positional = values[:2] if number == 3 else values
            if number == 15:
                positional = tuple(values[0] + values[1])
            setup += (
                "\n\ndef _with_argument_order(fn, ordered):\n"
                "    def checked(*args, **kwargs):\n"
                "        if args != ordered:\n"
                '            raise ValueError("位置引数を問題文の順番で渡してください。")\n'
                "        return fn(*args, **kwargs)\n"
                "    return checked\n"
                f"{name} = _with_argument_order({name}, {positional!r})"
            )
        # These two authored lessons return tuples; their JSON display values
        # have list syntax because JSON has no tuple type.
        if number in (16, 17):
            expected = tuple(expected)
        yield {"setup": setup, "args": repr(values)[1:-1], **pack_expected(expected)}


def compile_arguments(concept, seed):
    for lesson in LESSONS:
        number = lesson["number"]
        pid, version, stage = lesson["id"], lesson["version"], lesson["stage"]
        provided, invocation = "", ""
        if number in CALL_RULES:
            provided, _ = lesson["starter"].rsplit("\n", 1)
            starter = "result = "
            definition, *assignments = ast.parse(provided).body
            inputs = {node.targets[0].id: ast.literal_eval(node.value) for node in assignments}
            name = definition.name
            tests = list(call_tests(number, name, provided, inputs, lesson, seed))
            execution = {"mode": "script", "inputs": list(inputs), "globals": [name]}
            requirement = {"name": name, **CALL_RULES[number]}
        else:
            prefix, example = lesson["starter"].split("\n\nresult = ", 1)
            invocation = "result = " + example
            name = ast.parse(example).body[0].value.func.id
            if number in (8, 11):
                provided, starter = prefix, ""
            else:
                if number == 18:
                    provided, prefix = prefix.rsplit("\n\n", 1)
                starter = prefix + " "
            setup = provided if number == 18 else ""
            display_args = example[example.index("(") + 1 : -1].strip()
            cases = [(display_args, lesson["expected"]), *FUNCTION_CASES[number]]
            if seed == 99:
                cases[2:] = reversed(cases[2:])
            tests = [
                {
                    "setup": "\n\n".join(filter(None, (setup, FUNCTION_SETUP.get(args.split(",")[0])))),
                    "args": args,
                    **pack_expected(expected),
                }
                for args, expected in cases
            ]
            execution = {"mode": "function", "entrypoint": name}
            requirement = {
                "name": name,
                "variadic": [number in (7, 8, 9, 18), number in (10, 11, 12, 18)],
                "forward": number == 18,
            }
        result_type = {4: "list", 5: "list", 12: "dict", 16: "tuple", 17: "tuple"}
        if number in result_type:
            execution["result_type"] = result_type[number]
        yield {
            "id": pid,
            "family_id": pid,
            "version_id": f"{pid}@{version}",
            "content_version": version,
            "concept_id": CONCEPT_ID,
            "module_id": "python",
            "stage": stage,
            "type": "implementation",
            "difficulty": ("guided", "partial", "independent").index(stage) + 1,
            "title": lesson["title"],
            "description": lesson["task"],
            "learning_goal": concept["description"],
            "input_conditions": "",
            "output_conditions": lesson["task"],
            "starter_code": starter,
            "example": provided,
            "editable_regions": [{"start": len(starter), "end": len(starter)}],
            "hints": [lesson["hint"]],
            "solution": lesson["solution"],
            "explanation": lesson["hint"],
            "common_mistakes": [],
            "public_tests": tests[:2],
            "hidden_tests": tests[2:],
            "required_ast": "arguments:" + json.dumps(requirement, separators=(",", ":")),
            "check_dtype": True,
            "protect_inputs": True,
            "runtime": "browser",
            "packages": [],
            "prerequisites": concept["prerequisites"],
            "estimated_minutes": 2,
            "variant_seed": seed,
            "variant_generator": "argument-fixtures-v1",
            "tolerance": 1e-5,
            "workspace": {
                "mode": "function" if invocation else "script",
                "provided_code": provided,
                "task": lesson["task"],
                "structure": "function" if invocation else "script",
                "invocation": invocation,
                "authored": True,
                "hint_count": 1,
            },
            "execution": execution,
        }
