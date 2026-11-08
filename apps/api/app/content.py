import ast
import json
from .config import ROOT

DATA = json.loads((ROOT / "content/compiled/private.json").read_text(encoding="utf-8"))
VARIANTS = {42: DATA}
variant_path = ROOT / "content/compiled/variant-99.json"
if variant_path.exists():
    VARIANTS[99] = json.loads(variant_path.read_text(encoding="utf-8"))
PROBLEMS = {p["id"]: p for p in DATA["problems"]}
CONCEPTS = {c["id"]: c for c in DATA["concepts"]}
VERSIONS = {p["version_id"]: p for p in DATA["problems"]}
ARCHIVED_VARIANTS = {}
display_path = ROOT / "content/compiled/display.json"
DISPLAY = json.loads(display_path.read_text(encoding="utf-8")) if display_path.exists() else {}
for archived in sorted((ROOT / "content/versions").glob("*.json")):
    snapshot = json.loads(archived.read_text(encoding="utf-8"))
    for p in snapshot["problems"]:
        VERSIONS.setdefault(p["version_id"], p)
        ARCHIVED_VARIANTS[(p["version_id"], p.get("variant_seed", 42))] = p


def with_display(p):
    if p is None:
        return None
    metadata = DISPLAY.get(f"{p['version_id']}:{p.get('variant_seed', 42)}")
    if metadata is None:
        return p
    return p | {
        field: [case | {"expected_tuple_paths": paths}
                for case, paths in zip(p[field], metadata[field], strict=True)]
        for field in ("public_tests", "hidden_tests")
    }


def problem(version, seed=42):
    if "@" in version:
        return with_display(next(
            (p for p in VARIANTS.get(seed, DATA)["problems"] if p["version_id"] == version),
            ARCHIVED_VARIANTS.get((version, seed), VERSIONS.get(version)),
        ))
    return with_display(PROBLEMS.get(version))


def public_problem(p):
    p = with_display(p)
    return {k: v for k, v in p.items() if k not in ("solution", "hidden_tests", "hints")}


def reading_projects():
    from content.activities import READING_META, READING_QUESTIONS

    result = []
    for meta in READING_META:
        files = []
        for file in sorted((ROOT / "content/reading" / meta["id"]).glob("*.py")):
            code = file.read_text(encoding="utf-8")
            symbols = [
                {"name": n.name, "line": n.lineno}
                for n in ast.walk(ast.parse(code))
                if isinstance(n, (ast.FunctionDef, ast.ClassDef))
            ]
            files.append({"name": file.name, "code": code, "symbols": symbols})
        result.append(
            meta
            | {
                "files": files,
                "questions": READING_QUESTIONS[meta["id"]],
                "line_count": sum(len(f["code"].splitlines()) for f in files),
            }
        )
    return result


def public_activity(activity):
    return activity | {
        "questions": [{k: v for k, v in q.items() if k not in ("answer", "explanation")} for q in activity["questions"]]
    }
