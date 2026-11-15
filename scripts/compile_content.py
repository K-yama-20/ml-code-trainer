# ruff: noqa: E402
"""Compile public/private versioned artifacts from trusted, Git-owned source."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content.catalog import (
    CONCEPTS,
    MODULES,
    PREREQUISITES,
)
from content import arguments, arrays, axis_permutation, broadcasting, combining, conditional, files, indexing, iteration, reductions, reshaping
from content import autograd, checkpoints, data_loading, estimators, groupby, inference, losses, merging, metrics, missing, nn_modules, normalization, scaling, selection, splitting, tensor_ops, tensor_shapes, tensors, training
from content import sql_basics

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
        lessons, compile_lessons = ORDERED_LESSONS[c["id"]]
        concepts[-1].update(ordered_practice=True, problem_count=len(lessons))
        batch = list(compile_lessons(concepts[-1], seed))
        counts = Counter(p["stage"] for p in batch)
        assert len(lessons) == len(batch), c["id"]
        if any(counts[stage] < 2 for stage in sql_basics.STAGES):
            concepts[-1]["mastery_available"] = False
        problems.extend(batch)
    sql_concepts, sql_problems = sql_basics.compile_sql(seed, len(concepts))
    concepts.extend(sql_concepts)
    problems.extend(sql_problems)
    if not include_display:
        for p in problems:
            for case in p["public_tests"] + p["hidden_tests"]:
                case.pop("expected_tuple_paths", None)
    return {
        "version": 1,
        "modules": [*MODULES, sql_basics.MODULE],
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
        for seed, catalog in display_catalogs.items() for p in catalog["problems"] if "sql" not in p
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
