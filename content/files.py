"""The authored, ordered PY03 path, JSON and file exercises."""

import ast
import json
from pathlib import Path

from content.runner import pack, pack_expected

CONCEPT_ID = "PY03"
LESSONS = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
PREFIX = "result = "

# Separate inputs and independently specified expected results. No host paths
# are exposed; file fixtures create their own temporary directory per case.
ALTERNATIVES = {
    1: [('path = "archive/data.tar.gz"', ".gz"), ('path = "README"', "")],
    2: [('path = "runs/学習/log.txt"', "log.txt"), ('path = "checkpoint.pt"', "checkpoint.pt")],
    3: [('path = "archives/weights.tar.gz"', "weights.tar"), ('path = "README"', "README")],
    4: [
        ('root = Path("runs")\nsplit = "validation"\nfilename = "labels.json"', Path("runs/validation/labels.json")),
        ('root = Path("dataset/v2")\nsplit = "test"\nfilename = "images.csv"', Path("dataset/v2/test/images.csv")),
    ],
    5: [
        ('path = Path("logs/日本語.csv")', Path("logs/日本語.json")),
        ('path = Path("report.v2.csv")', Path("report.v2.json")),
    ],
    6: [
        ('path = Path("runs/loss.v2.csv")', Path("runs/loss.v2_backup.csv")),
        ('path = Path("metrics.json")', Path("metrics_backup.json")),
    ],
    7: [
        ('text = \'{"active": true, "seed": null}\'', {"active": True, "seed": None}),
        ('text = \'{"labels": ["犬", "猫"], "count": 0}\'', {"labels": ["犬", "猫"], "count": 0}),
    ],
    8: [
        ('text = \'{"model":{"name":"small","channels":[8,16]}}\'', [8, 16]),
        ('text = \'{"model":{"channels":[]}}\'', []),
    ],
    9: [('text = \'[{"epoch":3,"loss":0.9},{"epoch":1,"loss":0.1}]\'', [0.9, 0.1]), ('text = "[]"', [])],
    10: [
        ('config = {"enabled": True, "note": None}', '{"enabled": true, "note": null}'),
        ('config = {"layers": [8, 16], "lr": 0.0}', '{"layers": [8, 16], "lr": 0.0}'),
    ],
    11: [
        ('config = {"experiment": "物体検出", "epochs": 3}', '{"experiment": "物体検出", "epochs": 3}'),
        ('config = {"name": "犬と猫", "enabled": False}', '{"name": "犬と猫", "enabled": false}'),
    ],
    12: [
        ('config = {"z": 2, "a": {"y": 1, "b": 0}}', '{\n  "a": {\n    "b": 0,\n    "y": 1\n  },\n  "z": 2\n}'),
        ('config = {"z": [3, 1], "a": True}', '{\n  "a": true,\n  "z": [\n    3,\n    1\n  ]\n}'),
    ],
    13: [
        ('path.write_text("学習中\\n損失=0.5\\n", encoding="utf-8")', "学習中\n損失=0.5\n"),
        ('path.write_text("", encoding="utf-8")', ""),
    ],
    14: [
        ('path.write_text(" 猫 \\n\\n犬\\n", encoding="utf-8")', [" 猫 ", "", "犬"]),
        ('path.write_text("one\\ntwo", encoding="utf-8")', ["one", "two"]),
    ],
    15: [
        ('path.write_text(\'{"name":"学習","enabled":true}\', encoding="utf-8")', {"name": "学習", "enabled": True}),
        ('path.write_text("{}", encoding="utf-8")', {}),
    ],
    16: [('text = "損失=0.1\\n完了\\n"', "損失=0.1\n完了\n"), ('text = ""', "")],
    17: [
        ('path.write_text("既存ログ\\n", encoding="utf-8")\nnew_line = "次の行\\n"', "既存ログ\n次の行\n"),
        ('path.write_text("header", encoding="utf-8")\nnew_line = "+tail"', "header+tail"),
    ],
    18: [
        (
            'config = {"name": "画像分類", "enabled": True, "layers": [8, 16]}',
            {"name": "画像分類", "enabled": True, "layers": [8, 16]},
        ),
        ('config = {"lr": 0, "note": None}', {"lr": 0, "note": None}),
    ],
}


def compile_files(concept, seed):
    for lesson in LESSONS:
        number = lesson["number"]
        pid, version, stage = lesson["id"], lesson["version"], lesson["stage"]
        invocation = ""
        if number <= 15:
            provided, _ = lesson["starter"].rsplit("\n", 1)
            starter = PREFIX
        else:
            provided, invocation = lesson["starter"].rsplit("\n\n", 1)
            starter = ""
        fixture = provided.split("# 以下に答えを記入", 1)[0].rstrip()
        inputs = (
            ["root", "split", "filename"]
            if number == 4
            else ["text"]
            if 7 <= number <= 9
            else ["config"]
            if 10 <= number <= 12
            else ["path", "text"]
            if number == 16
            else ["path", "new_line"]
            if number == 17
            else ["path", "config"]
            if number == 18
            else ["path"]
        )
        imports = [
            ast.get_source_segment(fixture, node)
            for node in ast.parse(fixture).body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        base = "\n".join(imports)
        if number >= 13:
            base += '\nworkspace = TemporaryDirectory()\npath = Path(workspace.name) / "case.txt"'
        alternatives = ALTERNATIVES[number][:: (-1 if seed == 99 else 1)]
        tests = [
            {"setup": setup, "args": ", ".join(inputs), **pack_expected(expected)}
            for setup, expected in [
                (fixture, lesson["expected"]),
                *((base + "\n" + setup, pack(expected)) for setup, expected in alternatives),
            ]
        ]
        if number in (10, 11):
            for test in tests:
                test["comparison"] = "json_unicode" if number == 11 else "json"
        required = []
        if number <= 3:
            required.append("call:Path")
        if 7 <= number <= 9:
            required.append("call:loads")
        if 10 <= number <= 12:
            required.append("call:dumps")
        if number == 9:
            required.append("comprehension:list")
        if number == 18:
            required.append("call:dump")
        execution = {
            "mode": "script",
            "inputs": inputs,
            "globals": ["Path", "json"],
            "result_type": "path"
            if number in (4, 5, 6)
            else "dict"
            if number in (7, 15, 18)
            else "list"
            if number in (8, 9, 14)
            else "str",
        }
        if number >= 13:
            execution["temporary_workspace"] = True
        if invocation:
            execution["result_expression"] = invocation.removeprefix(PREFIX)
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
            "required_ast": "all:" + json.dumps(required),
            "check_dtype": True,
            "protect_inputs": True,
            "runtime": "browser",
            "packages": [],
            "prerequisites": concept["prerequisites"],
            "estimated_minutes": 2,
            "variant_seed": seed,
            "variant_generator": "file-fixtures-v1",
            "tolerance": 1e-5,
            "workspace": {
                "mode": "script",
                "provided_code": provided,
                "task": lesson["task"],
                "structure": "statements" if invocation else "script",
                "invocation": invocation,
                "authored": True,
                "hint_count": 1,
            },
            "execution": execution,
        }
