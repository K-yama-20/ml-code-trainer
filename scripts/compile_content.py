# ruff: noqa: E402
"""Compile public/private versioned artifacts from trusted, Git-owned source."""

import ast
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content.catalog import (
    CONCEPTS,
    MODULES,
    PRELUDE,
    TORCH_PRELUDE,
    FIXTURES,
    PREREQUISITES,
    COMMON_MISTAKES,
)
from content.runner import pack_expected
from content.drill_phase1 import improve
from content.concrete import improve_concrete
from content import arguments, arrays, axis_permutation, broadcasting, combining, conditional, files, indexing, iteration, reductions, reshaping
from content import autograd, checkpoints, data_loading, estimators, groupby, inference, losses, merging, metrics, missing, nn_modules, normalization, scaling, selection, splitting, tensor_ops, tensor_shapes, tensors, training

# Concepts compiled by content.ordered. Each module exports compile_<module name>.
AUTHORED_MODULES = [
    (module, getattr(module, "compile_" + module.__name__.rsplit(".", 1)[-1]))
    for module in (normalization, selection, missing, groupby, merging, splitting, scaling, estimators, metrics, tensors, tensor_shapes, tensor_ops, autograd, nn_modules, losses, training, data_loading, inference, checkpoints)
]

ORDERED_LESSONS = {
    iteration.CONCEPT_ID: (iteration.LESSONS, iteration.compile_iteration),
    arguments.CONCEPT_ID: (arguments.LESSONS, arguments.compile_arguments),
    files.CONCEPT_ID: (files.LESSONS, files.compile_files),
    arrays.CONCEPT_ID: (arrays.LESSONS, arrays.compile_arrays),
    indexing.CONCEPT_ID: (indexing.LESSONS, indexing.compile_indexing),
    reshaping.CONCEPT_ID: (reshaping.LESSONS, reshaping.compile_reshaping),
    axis_permutation.CONCEPT_ID: (axis_permutation.LESSONS, axis_permutation.compile_axis_permutation),
    reductions.CONCEPT_ID: (reductions.LESSONS, reductions.compile_reductions),
    broadcasting.CONCEPT_ID: (broadcasting.LESSONS, broadcasting.compile_broadcasting),
    combining.CONCEPT_ID: (combining.LESSONS, combining.compile_combining),
    conditional.CONCEPT_ID: (conditional.LESSONS, conditional.compile_conditional),
    **{module.CONCEPT_ID: (module.LESSONS, fn) for module, fn in AUTHORED_MODULES},
}


def setup_for(module, seed):
    base = f"seed = {seed}\nimport json, math, tempfile\nfrom pathlib import Path\n"
    if module == "python":
        return base
    if module == "pytorch":
        return base + TORCH_PRELUDE
    if module == "numpy":
        return (
            base
            + "import numpy as np\nrng=np.random.default_rng(seed)\nx=rng.normal(size=(3,4))\nv=np.array([0.,2.,-2.,4.])+seed\n"
        )
    if module == "pandas":
        return base + "import numpy as np\nimport pandas as pd\n" + FIXTURES
    return (
        base
        + PRELUDE.replace("import pandas as pd\n", "")
        + "\n".join(
            line for line in FIXTURES.splitlines() if not line.startswith("frame =")
        )
    )


def make_case(ex, module, call, seed):
    setup = setup_for(module, seed)
    env = {}
    exec(setup, env)
    # Bind the authored signature so the independent oracle uses actual inputs.
    exec(f"def oracle({ex.params}):\n    return {ex.oracle}", env)
    value = eval(f"oracle({call})", env)
    return dict(setup=setup, args=call, **pack_expected(value))


def variant_seed(problem_id, seed):
    return random.Random(f"v1:{problem_id}:{seed}").randint(1, 10000)


def buggy_code(concept_id, index, solution):
    """Realistic mistakes with a distinct failure mode for every bug family."""
    replacements = {
        ("PT01", 1): ("dtype=torch.int64", "dtype=torch.float32"),
        ("PT01", 3): ("dtype=torch.float64", "dtype=torch.float32"),
        ("PT01", 5): ("x.numel()", "x.dim()"),
        ("PT02", 1): ("x.reshape(-1)", "x.view(-1)"),
        ("PT02", 3): ("x.permute(0,3,1,2)", "x.reshape(0,3,1,2)"),
        ("PT02", 5): ("x.T.reshape(-1)", "x.reshape(-1)"),
        ("PT03", 1): ("keepdim=True", "keepdim=False"),
        ("PT03", 3): ("w.unsqueeze(1)", "w.unsqueeze(0)"),
        ("PT03", 5): ("x.mean()", "x.mean(dim=1)"),
        ("PT04", 1): ("requires_grad=True", "requires_grad=False"),
        ("PT04", 3): ("x.grad=None", "# x.grad is not reset"),
        ("PT04", 5): ("(x**3).sum().backward()", "(x**3).backward()"),
        ("PT05", 1): ("super().__init__()", "pass # Module not initialized"),
        ("PT05", 3): (
            "nn.Parameter(torch.tensor(values,dtype=torch.float32))",
            "torch.tensor(values,dtype=torch.float32)",
        ),
        ("PT05", 5): ("nn.Linear(4,2)", "nn.Linear(3,2)"),
        ("PT06", 1): ("(logits,labels)", "(logits.softmax(dim=1),labels)"),
        ("PT06", 3): ("labels.long()", "labels"),
        ("PT06", 5): ("reduction='sum'", "reduction='mean'"),
        ("PT07", 1): ("o.step()", "# o.step() is missing"),
        ("PT07", 3): ("o.zero_grad()", "# gradients accumulate"),
        ("PT07", 5): ("o.step()", "o.zero_grad() # gradients discarded before update"),
        ("PT08", 1): (
            "return len(DataLoader(d,batch_size=batch,drop_last=False))",
            "return n//batch",
        ),
        ("PT08", 3): ("drop_last=True", "drop_last=False"),
        ("PT08", 5): ("TensorDataset(x,y)", "TensorDataset(x,y.flip(0))"),
        ("PT09", 1): ("m.eval()", "m.train()"),
        ("PT09", 3): (
            "with torch.no_grad():",
            "if True: # gradient tracking remains enabled",
        ),
        ("PT09", 5): ("m.train(was)", "m.train()"),
        ("PT10", 1): ("['weight']", "['weights']"),
        ("PT10", 3): ("v.clone()", "v"),
        ("PT10", 5): ("b.eval()", "b.train()"),
    }
    before, after = replacements[(concept_id, index)]
    assert before in solution, (concept_id, index, before)
    return solution.replace(before, after, 1)


def compile_all(seed=42, include_display=False):
    problems, concepts = [], []
    for ci, c in enumerate(CONCEPTS):
        concepts.append(
            {k: v for k, v in c.items() if k != "exercises"}
            | {
                "prerequisites": PREREQUISITES[c["id"]],
                "order": ci,
            }
        )
        if c["id"] in ORDERED_LESSONS:
            lessons, compile_lessons = ORDERED_LESSONS[c["id"]]
            concepts[-1].update(ordered_practice=True, problem_count=len(lessons))
            problems.extend(compile_lessons(concepts[-1], seed))
            continue
        for i, ex in enumerate(c["exercises"]):
            stage = ["guided", "partial", "independent"][i // 2]
            typ = "implementation" if i >= 4 else "completion"
            if ci < 10 and i in (1, 3):
                typ = "prediction"
            if ci >= 20 and i in (1, 3, 5):
                typ = "bugfix"
            pid = f"{c['id']}-{i + 1:02}"
            effective = variant_seed(pid, seed)
            solution = (
                f"def solve({ex.params}):\n"
                + "\n".join("    " + line for line in ex.body.splitlines())
                + "\n"
            )
            lines = solution.splitlines()
            if stage == "guided":
                # Only replace a syntactic part; surrounding structure remains useful.
                tree = ast.parse(solution)
                returns = [
                    n
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Return) and n.value is not None
                ]
                node = returns[-1].value
                # Leave the operation visible, usually asking for an axis or API.
                keywords = [
                    k.value
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Call)
                    for k in n.keywords
                    if k.arg in ("axis", "dim", "dtype", "keepdims", "keepdim")
                ]
                if keywords:
                    node = keywords[-1]
                else:
                    constants = [
                        n
                        for n in ast.walk(node)
                        if isinstance(n, ast.Constant)
                        and isinstance(n.value, (int, float))
                        and not isinstance(n.value, bool)
                    ]
                    if constants:
                        node = constants[-1]
                # AST columns are UTF-8 byte offsets and the expression can
                # span several lines. Keep the exact text outside the slot.
                first = lines[node.lineno - 1].encode("utf-8")[:node.col_offset]
                last = lines[node.end_lineno - 1].encode("utf-8")[node.end_col_offset:]
                lines[node.lineno - 1 : node.end_lineno] = [(first + b"___" + last).decode("utf-8")]
                starter = "\n".join(lines) + "\n"
            elif stage == "partial":
                starter = f"def solve({ex.params}):\n    # {ex.title}\n    return ___\n"
            else:
                starter = (
                    f"def solve({ex.params}):\n    # ここに実装してください\n    pass\n"
                )
            description = ex.task
            if typ == "prediction":
                # The operation is intentionally shown; learner returns a prediction.
                description = (
                    "次の処理の戻り値を予測してください。solve内で同等の値を返します。\n\n"
                    + ex.task
                )
                observation = {
                    ("NP01", 1): "np.zeros((rows, cols)).shape",
                    ("NP02", 1): "x[:, :2].shape",
                    ("NP03", 1): "np.expand_dims(x, axis=0).shape",
                    ("NP04", 1): "x.transpose(2, 0, 1).shape",
                    ("NP05", 1): "x.sum(axis=0, keepdims=True).shape",
                    ("NP06", 1): "(a[:, None] * b[None, :]).shape",
                    ("NP07", 1): "np.stack([a, b], axis=0).shape",
                }.get((c["id"], i))
                example = (
                    "observed = " + observation
                    if observation
                    else ex.body.replace("return ", "observed = ")
                )
            else:
                example = c["example"]
            if typ == "bugfix":
                # Broken result in a real function, retained as an editable starting point.
                starter = buggy_code(c["id"], i, solution)
                description = (
                    "初期コードのBUGを修正し、次の条件を満たしてください。\n\n"
                    + description
                )
            cases = [
                make_case(ex, c["module_id"], call, effective) for call in ex.calls
            ]
            p = dict(
                id=pid,
                family_id=pid,
                version_id=f"{pid}@1",
                content_version=1,
                concept_id=c["id"],
                module_id=c["module_id"],
                stage=stage,
                type=typ,
                difficulty=i // 2 + 1,
                title=ex.title,
                description=description,
                learning_goal=c["description"],
                input_conditions=f"関数 solve({ex.params})。公開ケースで入力例を確認してください。",
                output_conditions=ex.task,
                starter_code=starter,
                example=example,
                editable_regions=[],
                hints=[
                    c["description"],
                    ex.note,
                    "戻り値のshape、型、境界条件を公開テストと比較してください。",
                ],
                solution=solution,
                explanation=ex.note,
                common_mistakes=COMMON_MISTAKES[c["id"]],
                public_tests=cases[:2],
                hidden_tests=cases[2:],
                required_ast=ex.api if typ != "prediction" else "",
                check_dtype=(c["id"] == "NP01" and i in (0, 3, 5)) or c["id"] == "PT01",
                protect_inputs=any(
                    text in ex.task for text in ("変更せず", "変更しない", "変えない")
                ),
                runtime="sandbox" if c["module_id"] == "pytorch" else "browser",
                packages={
                    "python": [],
                    "numpy": ["numpy"],
                    "pandas": ["numpy", "pandas"],
                    "sklearn": ["numpy", "scikit-learn"],
                    "pytorch": ["torch"],
                }[c["module_id"]],
                prerequisites=concepts[-1]["prerequisites"],
                estimated_minutes=i // 2 + 1,
                variant_seed=seed,
                variant_generator="reproducible-random-v1",
                tolerance=1e-5,
            )
            p = improve(p, make_case, ex, c["module_id"], effective)
            problems.append(improve_concrete(p, make_case, ex, c["module_id"], effective))
    if not include_display:
        for p in problems:
            for case in p["public_tests"] + p["hidden_tests"]:
                case.pop("expected_tuple_paths", None)
    return {
        "version": 1,
        "modules": MODULES,
        "concepts": concepts,
        "problems": problems,
    }


def public_problem(p):
    return {
        k: v for k, v in p.items() if k not in ("solution", "hidden_tests", "hints")
    }


def main():
    display_catalogs = {seed: compile_all(seed, include_display=True) for seed in (42, 99)}
    # Keep published grading definitions byte-for-byte compatible. Type paths
    # are an additive display sidecar, keyed by exact problem version and seed.
    display = {
        f"{p['version_id']}:{seed}": {
            field: [case["expected_tuple_paths"] for case in p[field]]
            for field in ("public_tests", "hidden_tests")
        }
        for seed, catalog in display_catalogs.items() for p in catalog["problems"]
    }
    data = compile_all()
    target = ROOT / "content" / "compiled"
    target.mkdir(exist_ok=True)
    display_path = target / "display.json"
    if display_path.exists():
        # Retain display types for exact versions moved into content/versions.
        display = json.loads(display_path.read_text(encoding="utf-8")) | display
    (target / "display.json").write_text(
        json.dumps(display, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (target / "private.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    public = data | {"problems": [public_problem(p) for p in display_catalogs[42]["problems"]]}
    (target / "public.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (target / "variant-99.json").write_text(
        json.dumps(compile_all(99), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "sha256": hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest(),
                "concepts": len(data["concepts"]),
                "problems": len(data["problems"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Compiled {len(data['concepts'])} concepts / {len(data['problems'])} problems"
    )


if __name__ == "__main__":
    main()
