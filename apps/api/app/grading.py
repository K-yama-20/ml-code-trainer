"""Pure trusted comparison and AST checks. No learner code is evaluated here."""

import ast
import json
import math


from content.runner import check_syntax


def static_check(code: str, required: str) -> bool:
    return check_syntax(ast.parse(code), required)


def equivalent(actual, expected, tolerance=1e-5, check_dtype=False, relative=False):
    """Compare packed values. ``relative`` drops the absolute floor so values
    near 1e-16 (log1p/expm1 drills) are not accepted as 0."""
    if isinstance(expected, bool):
        return actual is expected
    if isinstance(expected, (int, float)):
        return (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and math.isclose(actual, expected, rel_tol=tolerance,
                             abs_tol=0.0 if relative else tolerance)
        )
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        keys = set(expected)
        if not check_dtype:
            keys -= {"dtype"}
        actual_keys = set(actual) - ({"dtype"} if not check_dtype else set())
        if keys != actual_keys:
            return False
        return all(k in actual and equivalent(actual[k], expected[k], tolerance, check_dtype, relative) for k in keys)
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(equivalent(a, b, tolerance, check_dtype, relative) for a, b in zip(actual, expected))
        )
    return actual == expected


def judge(outputs, cases, code, required="", check_dtype=False, protect_inputs=False, public_count=0):
    try:
        valid_static = static_check(code, required)
    except SyntaxError as err:
        return {
            "verdict": "Syntax Error",
            "passed_tests": 0,
            "total_tests": len(cases),
            "stderr": str(err),
            "error_line": err.lineno,
            "tests": [],
        }
    tests = []
    for i, case in enumerate(cases):
        out = outputs[i] if i < len(outputs) else {"error": "Missing result"}
        actual, expected = out.get("value"), case["expected"]
        comparison = case.get("comparison", "exact")
        if comparison in ("json", "json_unicode"):
            try:
                unicode_ok = comparison != "json_unicode" or all(
                    char in actual for char in expected if ord(char) > 127
                )
                ok = (isinstance(actual, str) and unicode_ok
                      and equivalent(json.loads(actual), json.loads(expected), check_dtype=check_dtype))
            except (ValueError, TypeError):
                ok = False
        else:
            ok = "value" in out and equivalent(
                actual, expected, check_dtype=check_dtype, relative=comparison == "relative"
            )
        if protect_inputs and out.get("mutated_inputs"):
            ok = False
        if out.get("replaced_inputs") or out.get("wrong_type"):
            ok = False
        error = (
            "用意された入力変数が再定義されています。提供された入力を使って計算してください。"
            if out.get("replaced_inputs")
            else (
                "入力データが変更されています。入力はそのまま使い、結果をresultに代入してください。"
                if protect_inputs and out.get("mutated_inputs")
                else "resultの型を問題文に合わせてください。"
                if out.get("wrong_type")
                else out.get("error", "")
            )
        )
        tests.append({"name": f"Test {i + 1}", "passed": ok, "error": error})
        if i < public_count:
            tests[-1].update(actual=out.get("value"), expected=case["expected"])
            if "tuple_paths" in out:
                tests[-1]["actual_tuple_paths"] = out["tuple_paths"]
            if "expected_tuple_paths" in case:
                tests[-1]["expected_tuple_paths"] = case["expected_tuple_paths"]
    passed = sum(t["passed"] for t in tests)
    errors = [o for o in outputs if "error" in o]
    verdict = "Accepted" if passed == len(cases) and valid_static else "Wrong Answer"
    if errors:
        verdict = "Syntax Error" if errors[0].get("kind") == "SyntaxError" else "Runtime Error"
    return {
        "verdict": verdict,
        "passed_tests": passed,
        "total_tests": len(cases),
        "tests": tests,
        "stderr": errors[0]["error"]
        if errors
        else ("指定されたAPI・構文を使用してください。" if not valid_static else ""),
        "error_line": errors[0].get("line") if errors else None,
    }
