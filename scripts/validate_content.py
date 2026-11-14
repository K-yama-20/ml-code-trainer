# ruff: noqa: E402
"""Execute trusted reference and representative wrong answers, including edges."""

import argparse
import ast
import collections
import io
import re
import tokenize
import json
import math
from pathlib import Path
import sys
import time
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compile_content import compile_all, public_problem
from content.runner import pack, run_payload, wrong_result_type
from content.activities import DEEP_DIVES, READING_META, READING_QUESTIONS
from apps.api.app.grading import judge


INVALID_OPERATORS = frozenset("≠＝×÷−–—﹣－＂＇‘’“”≤≥")
PYTHON_FENCE = re.compile(r"^```(?:python|py)\s*\n(.*?)^```", re.M | re.S)


def check_python(source, label, mode="exec"):
    """Check Python only. Unicode in a comment or a literal is valid."""
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if tokenize.tok_name[token.type] in {"STRING", "COMMENT", "FSTRING_MIDDLE", "TSTRING_MIDDLE"}:
                continue
            operator = next((char for char in token.string if char in INVALID_OPERATORS), None)
            if operator:
                raise ValueError(f"{label}:{token.start[0]}: invalid Python operator {operator!r}")
        return ast.parse(source, filename=label, mode=mode)
    except (SyntaxError, tokenize.TokenError) as exc:
        raise ValueError(f"{label}: {exc}") from exc


def check_display(p):
    label = p["version_id"]
    workspace = p.get("workspace") or {}
    provided = workspace.get("provided_code", "")
    solution = p["solution"]
    check_python(solution, f"{label}:solution")
    starter = p["starter_code"]
    if p["type"] == "bugfix":
        check_python(starter, f"{label}:starter")
    else:
        # A starter is intentionally unfinished. Only a completed editor
        # document may be checked as executable code.
        assert starter.count("___") <= 1, label
        if "___" in starter and p["type"] != "prediction":
            prefix, suffix = starter.split("___")
            assert solution.startswith(prefix) and solution.endswith(suffix), (
                label, "reference answer must fit the editor's protected scaffold"
            )
            fragment = solution[len(prefix):len(solution) - len(suffix)]
            assert fragment.strip(), label

    if workspace.get("mode") == "prediction":
        source, output = provided, "observed"
    else:
        invocation = workspace.get("invocation", "")
        source = "\n".join((provided, solution, invocation))
        output = "result" if workspace else None
    tree = check_python(source, f"{label}:completed workspace")
    if output:
        env = {}
        exec(compile(tree, f"{label}:completed workspace", "exec"), env)
        assert not wrong_result_type(env[output], (p.get("execution") or {}).get("result_type")), label
        actual = pack(
            env[output],
            preserve_scalar_array=(p.get("execution") or {}).get("result_type") == "array",
        )
        display = judge([{"value": actual}], p["public_tests"][:1],
                        solution, p["required_ast"], p["check_dtype"])
        assert display["verdict"] == "Accepted", (label, "display", display)
    for case in p["public_tests"] + p["hidden_tests"]:
        check_python(case["setup"], f"{label}:test setup")
        check_python(f"_capture({case['args']})", f"{label}:test arguments", "eval")
    for prose in [*p["hints"], p["explanation"], *p["common_mistakes"]]:
        snippets = PYTHON_FENCE.findall(prose)
        if prose.startswith("解答部分は次の形で書けます。\n"):
            snippets.append(prose.split("\n", 1)[1])
        for snippet in snippets:
            check_python(snippet, f"{label}:Python snippet")


def same_content(a, b):
    """Exact equality, except floats may differ by platform rounding noise.

    Some expected values (e.g. scikit-learn solver output) differ in the last
    bits between Windows and Linux. The tolerance is far tighter than grading's
    1e-5, so any real content change still counts as a change.
    """
    if isinstance(a, float) or isinstance(b, float):
        return (isinstance(a, (int, float)) and isinstance(b, (int, float))
                and not isinstance(a, bool) and not isinstance(b, bool)
                and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same_content(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_content(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def first_difference(a, b, path="$"):
    """Describe where two catalog values first differ, for readable failures."""
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return f"{path}: keys {sorted(a.keys() ^ b.keys())}"
        return next((d for k in a if (d := first_difference(a[k], b[k], f"{path}.{k}"))), None)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        return next((d for i, (x, y) in enumerate(zip(a, b)) if (d := first_difference(x, y, f"{path}[{i}]"))), None)
    return None if same_content(a, b) else f"{path}: {a!r:.200} != {b!r:.200}"


def check_versions(latest):
    seen = {}
    archives = [json.loads(f.read_text(encoding="utf-8")) for f in
                sorted((ROOT / "content" / "versions").glob("*.json"))]
    for catalog in [*archives, *latest]:
        assert len({p["version_id"] for p in catalog["problems"]}) == len(catalog["problems"])
        for p in catalog["problems"]:
            assert p["family_id"] == p["id"]
            assert p["version_id"] == f"{p['id']}@{p['content_version']}"
            key = p["version_id"], p["variant_seed"]
            old = seen.setdefault(key, p)
            assert same_content(old, p), (key, "version changed without a bump", first_difference(old, p))


def check_reference(p):
    cases = p["public_tests"] + p["hidden_tests"]
    assert all(p[field] for field in ("title", "description", "hints", "solution", "explanation")), p["id"]
    assert len(p["hints"]) == (p.get("workspace") or {}).get("hint_count", 3), p["id"]
    code = p["solution"]
    output = run_payload({"code": code, "cases": cases, "execution": p.get("execution", {})})
    return judge(output["outputs"], cases, code, p["required_ast"], p["check_dtype"], p.get("protect_inputs", False))


def validate_concept(concept_id):
    """Quickly test the compiled data for one edited concept."""
    total = cases = 0
    for name in ("private.json", "variant-99.json"):
        data = json.loads((ROOT / "content" / "compiled" / name).read_text(encoding="utf-8"))
        assert len({p["id"] for p in data["problems"]}) == len(data["problems"]), name
        concept = next(c for c in data["concepts"] if c["id"] == concept_id)
        problems = [p for p in data["problems"] if p["concept_id"] == concept_id]
        assert len(problems) == concept.get("problem_count", 6)
        for p in problems:
            check_display(p)
            result = check_reference(p)
            assert result["verdict"] == "Accepted", (p["version_id"], name, result)
            total += 1
            cases += result["total_tests"]
    print(f"{concept_id}: {total // 2} questions, two variants, {cases} reference cases passed")



def validate():
    started = time.monotonic()
    data = compile_all()
    assert len(data["concepts"]) == 30
    problem_count = sum(c.get("problem_count", 6) for c in data["concepts"])
    assert len(data["problems"]) == problem_count
    assert len({p["id"] for p in data["problems"]}) == problem_count
    distribution = collections.Counter(
        (p["stage"], p["type"]) for p in data["problems"]
    )
    assert distribution == collections.Counter(
        {
            ("guided", "completion"): 28,
            ("partial", "completion"): 28,
            ("independent", "implementation"): 94,
            ("guided", "implementation"): 66,
            ("partial", "implementation"): 66,
            ("guided", "bugfix"): 10,
            ("partial", "bugfix"): 10,
            ("independent", "bugfix"): 10,
        }
    ), distribution
    for c in data["concepts"]:
        ps = [p for p in data["problems"] if p["concept_id"] == c["id"]]
        count_per_stage = c.get("problem_count", 6) // 3
        assert collections.Counter(p["stage"] for p in ps) == dict.fromkeys(
            ("guided", "partial", "independent"), count_per_stage
        )
        assert len({p["title"] for p in ps}) == c.get("problem_count", 6)
    failures = []
    count = 0
    catalogs = [data, compile_all(99)]
    check_versions(catalogs)
    compiled = ROOT / "content" / "compiled"
    for name, expected in (
        ("private.json", data),
        ("variant-99.json", catalogs[1]),
        ("public.json", data | {"problems": [public_problem(p) for p in compile_all(include_display=True)["problems"]]}),
    ):
        assert same_content(json.loads((compiled / name).read_text(encoding="utf-8")), expected), (
            f"{name} is stale. Run scripts/compile_content.py."
        )
    for seed, catalog in zip((42, 99), catalogs, strict=True):
        for p in catalog["problems"]:
            check_display(p)
            cases = p["public_tests"] + p["hidden_tests"]
            minimum = 1 if p["type"] == "prediction" else (
                3 if p["variant_generator"] in (
                    "file-fixtures-v1", "array-fixtures-v1", "indexing-fixtures-v1",
                    "reshaping-fixtures-v1", "axis-permutation-fixtures-v1", "reduction-fixtures-v1",
                    "broadcasting-fixtures-v1", "combining-fixtures-v1", "conditional-fixtures-v1"
                ) else 4
            )
            assert len(cases) >= minimum
            result = check_reference(p)
            if result["verdict"] != "Accepted":
                failures.append({"id": p["id"], "seed": seed, "result": result})
            wrong = "def solve(*args, **kwargs):\n    return None\n"
            bad = run_payload({"code": wrong, "cases": cases, "execution": p.get("execution", {})})
            assert judge(bad["outputs"], cases, wrong)["verdict"] != "Accepted", p["id"]
            if p["type"] == "bugfix":
                bug = run_payload({"code": p["starter_code"], "cases": cases, "execution": p.get("execution", {})})
                assert (
                    judge(
                        bug["outputs"],
                        cases,
                        p["starter_code"],
                        p["required_ast"],
                        p["check_dtype"],
                    )["verdict"]
                    != "Accepted"
                ), p["id"]
            count += len(cases)
    assert compile_all(42) == compile_all(42), "Non-reproducible variant"
    assert len(DEEP_DIVES) == 12 and len(READING_META) == 3
    for dive in DEEP_DIVES:
        check_python(dive["code"], f"Deep Dive {dive['id']}")
    for meta in READING_META:
        files = list((ROOT / "content" / "reading" / meta["id"]).glob("*.py"))
        lines = 0
        for file in files:
            source = file.read_text(encoding="utf-8")
            check_python(source, str(file))
            lines += len(source.splitlines())
        assert len(READING_QUESTIONS[meta["id"]]) == 8
        for q in READING_QUESTIONS[meta["id"]]:
            assert q["symbol"] in (
                ROOT / "content" / "reading" / meta["id"] / q["file"]
            ).read_text(encoding="utf-8")
        print(f"Reading: {meta['id']} / {len(files)} files / {lines} lines")
    report = {
        "problems": problem_count,
        "concepts": 30,
        "seeds": 2,
        "reference_cases": count,
        "wrong_answers_rejected": problem_count * 2,
        "completed_workspaces": problem_count * 2,
        "invalid_python_unicode": 0,
        "failures": failures,
        "deep_dives": 12,
        "reading_projects": 3,
        "seconds": round(time.monotonic() - started, 2),
    }
    target = ROOT / "artifacts"
    target.mkdir(exist_ok=True)
    (target / "content-validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if failures:
        for f in failures:
            print(json.dumps(f, ensure_ascii=False))
        raise SystemExit(f"{len(failures)} reference failures")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept", help="Validate just one concept from the compiled catalog")
    options = parser.parse_args()
    temp = ROOT / "artifacts" / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temp)
    if options.concept:
        validate_concept(options.concept)
    else:
        validate()
