"""Untrusted runtime payload. Executed only in Pyodide, Modal, or content QA subprocess.

Contains no expected answers, hidden assertions, credentials, or DB access.
"""

import builtins
import contextlib
import io
import json
import traceback
import time
import ast
from types import FunctionType
from pathlib import Path, PurePath


def script_contract(code, definition):
    """Validate only the learner block; fixtures are supplied by the trusted caller."""
    tree = ast.parse(code, filename="<student>")
    protected = set(definition.get("inputs", []))

    class ProvidedWrites(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in protected:
                raise ValueError(
                    f"入力の{node.id}は用意されています。初期化し直さず、resultに結果を代入してください。"
                )

        def visit_FunctionDef(self, node):
            return  # Local names belong to the function; runtime checks cover mutations.

        def visit_AugAssign(self, node):
            if definition.get("allow_input_mutation"):
                self.visit(node.value)
            else:
                self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef

        def visit_ListComp(self, node):
            return

        visit_SetComp = visit_ListComp
        visit_DictComp = visit_ListComp
        visit_GeneratorExp = visit_ListComp

    ProvidedWrites().visit(tree)
    result_writes = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id == "result"
    ]
    # Do not mistake an accumulator or a conditional algorithm for a copied
    # answer. This bounded check rejects a single direct literal assignment.
    if definition.get("constant_goal") and len(result_writes) == 1:
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                if any(isinstance(t, ast.Name) and t.id == "result" for t in targets):
                    try:
                        ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
                    else:
                        raise ValueError(
                            "表示された答えの直接代入ではなく、指定された操作でresultを求めてください。"
                        )


def pack(value, preserve_scalar_array=False, *, tuple_paths=None, _path=()):
    def child(item, key):
        return pack(item, tuple_paths=tuple_paths, _path=(*_path, key))

    if isinstance(value, PurePath):
        return {"kind": "path", "value": value.as_posix()}
    name = type(value).__module__.split(".")[0]
    if name == "torch":
        value = value.detach().cpu()
        return {
            "kind": "tensor",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "device": str(value.device),
            "data": child(value.tolist(), "data"),
        }
    if name == "pandas":
        if getattr(value, "ndim", 0) == 2:
            return {
                "kind": "dataframe",
                "columns": child(value.columns.tolist(), "columns"),
                "index": child(value.index.tolist(), "index"),
                "data": child(value.to_numpy().tolist(), "data"),
            }
        return {
            "kind": "series",
            "index": child(value.index.tolist(), "index"),
            "data": child(value.tolist(), "data"),
        }
    if name == "numpy":
        import numpy as np

        if isinstance(value, np.ndarray) and (value.ndim > 0 or preserve_scalar_array):
            return {
                "kind": "array",
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "data": child(value.tolist(), "data"),
            }
        return pack(value.item(), tuple_paths=tuple_paths, _path=_path)
    if isinstance(value, dict):
        return {str(k): child(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if isinstance(value, tuple) and tuple_paths is not None:
            tuple_paths.append(list(_path))
        return [child(v, i) for i, v in enumerate(value)]
    if isinstance(value, float):
        if value != value:
            return "__NaN__"
        if abs(value) == float("inf"):
            return "__Inf__" if value > 0 else "__-Inf__"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Unsupported return type: {type(value).__name__}")


def pack_expected(value, preserve_scalar_array=False):
    """Display-only type paths live outside the unchanged comparison value."""
    paths = []
    expected = pack(value, preserve_scalar_array, tuple_paths=paths)
    return {"expected": expected, "expected_tuple_paths": paths}


class LimitedOutput(io.StringIO):
    def write(self, text):
        remaining = 32768 - self.tell()
        if remaining > 0:
            super().write(text[:remaining])
        return len(text)


def wrong_result_type(value, expected):
    if expected == "number":
        from numbers import Real

        return not isinstance(value, Real) or isinstance(value, bool)
    if expected == "array":
        import numpy as np

        return not isinstance(value, np.ndarray)
    if expected == "path":
        return not isinstance(value, Path)
    if expected == "str":
        return not isinstance(value, str)
    if expected == "dict":
        return not isinstance(value, dict)
    if expected == "tuple":
        return not isinstance(value, tuple)
    if expected in {"list", "list_of_pairs"}:
        return not isinstance(value, list) or (
            expected == "list_of_pairs"
            and any(not isinstance(pair, tuple) or len(pair) != 2 for pair in value)
        )
    return False


def snapshot_inputs(args, kwargs):
    # Some exercises pass a fixture function to the learner. Its identity is
    # fixed in the call, while the other arguments still need mutation checks.
    return pack((
        tuple(None if isinstance(value, FunctionType) else value for value in args),
        {key: None if isinstance(value, FunctionType) else value for key, value in kwargs.items()},
    ))


def run_payload(payload, timings=None):
    results = []
    stdout, stderr = LimitedOutput(), LimitedOutput()
    clock = time.perf_counter
    student_seconds = 0.0
    for case in payload["cases"]:
        cleanup = None
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                env = {"__name__": "__exercise__", "seed": payload.get("seed", 1)}
                exec(compile(case["setup"], "<fixture>", "exec"), env)
                definition = payload.get("execution", {})
                if definition.get("temporary_workspace"):
                    cleanup = env["workspace"].cleanup
                args, kwargs = eval(
                    "_capture(" + case["args"] + ")",
                    env,
                    {"_capture": lambda *args, **kwargs: (args, kwargs)},
                )
                before = snapshot_inputs(args, kwargs)
                input_bindings = {}
                if definition.get("mode") == "script":
                    script_contract(payload["code"], definition)
                    input_bindings = dict(zip(definition["inputs"], args, strict=True))
                    input_bindings.update(kwargs)
                    env = (
                        {"__name__": "__exercise__"}
                        | {
                            name: env[name]
                            for name in definition["globals"]
                            if name in env
                        }
                        | input_bindings
                    )
                observation_env = env.copy()
                student_started = clock()
                try:
                    exec(compile(payload["code"], "<student>", "exec"), env)
                    if definition.get("result_expression"):
                        value = eval(
                            compile(definition["result_expression"], "<observation>", "eval"),
                            observation_env,
                        )
                    elif definition.get("mode") == "script" and "result" not in env:
                        raise ValueError(
                            "計算した結果をresultに代入してください。printで表示するだけでは解答になりません。"
                        )
                    else:
                        value = (
                            env["result"]
                            if definition.get("mode") == "script"
                            else env[definition.get("entrypoint", "solve")](*args, **kwargs)
                        )
                finally:
                    student_seconds += clock() - student_started
                tuple_paths = []
                packed = pack(value, preserve_scalar_array=definition.get("result_type") == "array",
                              tuple_paths=tuple_paths)
                results.append(
                    {
                        "value": packed,
                        "tuple_paths": tuple_paths,
                        **({"wrong_type": True} if wrong_result_type(value, definition.get("result_type")) else {}),
                        "mutated_inputs": before != snapshot_inputs(args, kwargs),
                        "replaced_inputs": any(
                            env.get(k) is not v for k, v in input_bindings.items()
                        ),
                    }
                )
        except BaseException as err:
            frames = traceback.extract_tb(err.__traceback__)
            line = getattr(err, "lineno", None)
            for f in frames:
                if f.filename == "<student>":
                    line = f.lineno
            results.append(
                {"error": str(err)[:2000], "kind": type(err).__name__, "line": line}
            )
        finally:
            if cleanup is not None:
                cleanup()
    if timings is not None:
        timings["student_ms"] = student_seconds * 1000
    return {
        "outputs": results,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
    }


# Only a conservative subset may share the browser runtime. Arbitrary Python
# still runs, but its worker is discarded afterwards. The whitelist excludes
# reflective names, arbitrary imports, attribute writes and stateful APIs.
_REUSABLE_NODES = {
    "Module", "Assign", "AnnAssign", "AugAssign", "Expr", "Constant",
    "Name", "Load", "Store", "List", "Tuple", "Dict", "Set", "Starred",
    "Subscript", "Slice", "Attribute", "Call", "keyword", "Return",
    "FunctionDef", "arguments", "arg", "For", "While", "If", "IfExp",
    "Pass", "Break", "Continue", "ListComp", "DictComp", "SetComp",
    "GeneratorExp", "comprehension", "Import", "alias", "BinOp", "UnaryOp",
    "BoolOp", "Compare", "Add", "Sub", "Mult", "Div", "FloorDiv", "Mod",
    "Pow", "MatMult", "BitAnd", "BitOr", "BitXor", "Invert", "UAdd",
    "USub", "Not", "And", "Or", "Eq", "NotEq", "Lt", "LtE", "Gt",
    "GtE", "In", "NotIn", "Is", "IsNot",
    "ImportFrom", "JoinedStr", "FormattedValue",
}
_REUSABLE_ATTRIBUTES = {
    "array", "asarray", "arange", "linspace", "ones", "zeros", "full",
    "ones_like", "zeros_like", "reshape", "ravel", "flatten",
    "transpose", "swapaxes", "moveaxis", "expand_dims", "squeeze", "concatenate", "stack",
    "vstack", "hstack", "broadcast_to", "mean", "median", "std", "var",
    "sum", "min", "max", "argmin", "argmax", "abs", "clip", "where", "sqrt",
    "exp", "log", "log1p", "isnan", "isfinite", "unique", "sort", "argsort",
    "astype", "copy", "tolist", "item", "shape", "size", "ndim", "dtype",
    "T", "int32", "int64", "float32", "float64", "bool_", "dot", "matmul",
    "all", "any", "maximum", "minimum", "get", "items", "keys", "values",
    "append", "extend", "count", "index", "startswith", "endswith",
    "lower", "upper", "strip", "split", "join", "ceil", "floor",
    "DataFrame", "Series", "iloc", "loc", "groupby", "size", "isna",
    "dropna", "fillna", "ffill", "assign", "concat", "merge", "index", "columns",
    "reset_index", "to_numpy", "group", "score", "value", "linalg", "norm",
    "count_nonzero",
}


_REUSABLE_BUILTINS = set("""
    abs all any bool dict divmod enumerate filter float int isinstance len list
    map max min next pow print range repr reversed round set sorted str sum tuple zip
""".split())
_OTHER_BUILTINS = frozenset(vars(builtins)) - _REUSABLE_BUILTINS


def reusable_browser_code(tree, path_inputs=()):
    # These extra APIs are allowed only on their known module or Path receiver.
    json_names, pathlib_names, constructors = {"json"}, set(), {"Path"}
    bindings, writes = {}, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name
                json_names.discard(local)
                constructors.discard(local)
                if alias.name == "json":
                    json_names.add(local)
                if alias.name == "pathlib":
                    pathlib_names.add(local)
        if isinstance(node, ast.ImportFrom) and node.module == "pathlib":
            constructors.update(alias.asname or alias.name for alias in node.names if alias.name == "Path")
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            writes.add(node.id)
        if isinstance(node, ast.arg):
            writes.add(node.arg)
        if isinstance(node, ast.FunctionDef):
            writes.add(node.name)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings.setdefault(target.id, []).append(node.value)
    json_names -= writes
    pathlib_names -= writes
    constructors -= writes
    paths = set(path_inputs) - writes

    def path_value(node, seen=frozenset()):
        if isinstance(node, ast.Name):
            if node.id in paths:
                return True
            values = bindings.get(node.id, [])
            return len(values) == 1 and node.id not in seen and path_value(values[0], seen | {node.id})
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return path_value(node.left, seen)
        if isinstance(node, ast.Attribute) and node.attr == "parent":
            return path_value(node.value, seen)
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                return fn.id in constructors
            if isinstance(fn, ast.Attribute):
                return (
                    fn.attr == "Path" and isinstance(fn.value, ast.Name) and fn.value.id in pathlib_names
                    or fn.attr in {"with_suffix", "with_name", "joinpath"} and path_value(fn.value, seen)
                )
        return False

    for node in ast.walk(tree):
        if type(node).__name__ not in _REUSABLE_NODES:
            return False
        if isinstance(node, ast.Attribute):
            standard = (
                node.attr in {"loads", "dumps"}
                and isinstance(node.value, ast.Name) and node.value.id in json_names
                or node.attr == "Path" and isinstance(node.value, ast.Name) and node.value.id in pathlib_names
                or node.attr in {"name", "stem", "suffix", "parent", "with_suffix", "with_name", "joinpath"}
                and path_value(node.value)
            )
            if not isinstance(node.ctx, ast.Load) or not (standard or node.attr in _REUSABLE_ATTRIBUTES):
                return False
        if isinstance(node, ast.Name) and (
            node.id.startswith("_") or node.id in _OTHER_BUILTINS
        ):
            return False
        if isinstance(node, ast.Import) and any(
            alias.name not in {"numpy", "pandas", "math", "json", "pathlib"} for alias in node.names
        ):
            return False
        if isinstance(node, ast.ImportFrom) and (
            node.level
            or node.module not in {"json", "pathlib"}
            or any(alias.name not in ({"Path"} if node.module == "pathlib" else {"loads", "dumps"})
                   for alias in node.names)
        ):
            return False
        # Decorators run code at definition time and may alter module state.
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            return False
    return True


def check_comprehension(tree, requirement):
    # Inspect the result expression and the values assigned to names it uses.
    # Unrelated expressions elsewhere in the answer do not satisfy the task.
    bindings = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            bindings.update((t.id, stmt.value) for t in targets if isinstance(t, ast.Name))

    def nodes(expr):
        if expr is None:
            return
        visited = set()
        pending = [expr]
        while pending:
            node = pending.pop()
            if id(node) in visited:
                continue
            visited.add(id(node))
            yield node
            pending.extend(ast.iter_child_nodes(node))
            if isinstance(node, ast.Name) and node.id in bindings:
                pending.append(bindings[node.id])

    def calls_builtin(expr, name):
        for node in nodes(expr):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            seen = set()
            while isinstance(callee, ast.Name) and callee.id in bindings and callee.id not in seen:
                seen.add(callee.id)
                callee = bindings[callee.id]
            if isinstance(callee, ast.Name) and callee.id == name:
                return True
            if (isinstance(callee, ast.Attribute) and callee.attr == name
                    and isinstance(callee.value, ast.Name) and callee.value.id == "builtins"):
                return True
        return False

    kind = ast.DictComp if requirement.startswith("dict") else ast.ListComp
    for comp in nodes(bindings.get("result")):
        if not isinstance(comp, kind):
            continue
        if requirement in {"list", "dict"}:
            return True
        if requirement == "filter" and any(gen.ifs for gen in comp.generators):
            return True
        if requirement == "nested" and len(comp.generators) >= 2:
            return True
        name = "zip" if requirement == "dict-zip" else requirement
        if name in {"zip", "enumerate"} and any(calls_builtin(gen.iter, name) for gen in comp.generators):
            return True
    return False


def check_syntax(tree, required):
    if required.startswith("not:"):
        return not check_syntax(tree, required.removeprefix("not:"))
    if required.startswith("literal:"):
        value = json.loads(required.removeprefix("literal:"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Constant, ast.UnaryOp)):
                try:
                    if ast.literal_eval(node) == value:
                        return True
                except (ValueError, TypeError):
                    pass
        return False
    if required.startswith("attr:"):
        return any(
            isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
            and node.attr == required.removeprefix("attr:")
            for node in ast.walk(tree)
        )
    if required.startswith("all:"):
        return all(check_syntax(tree, item) for item in json.loads(required.removeprefix("all:")))
    if required.startswith("arguments:"):
        return check_argument_syntax(tree, json.loads(required.removeprefix("arguments:")))
    if required.startswith("call-keywords:"):
        return check_call_keywords(tree, json.loads(required.removeprefix("call-keywords:")))
    if required.startswith("comprehension:"):
        return check_comprehension(tree, required.removeprefix("comprehension:"))
    if required.startswith(("call:", "call-count:")):
        parts = required.split(":")
        name = parts[1]
        count = sum(
            isinstance(n, ast.Call) and (
                isinstance(n.func, ast.Name) and n.func.id == name
                or isinstance(n.func, ast.Attribute) and n.func.attr == name
            )
            for n in ast.walk(tree)
        )
        return count == int(parts[2]) if parts[0] == "call-count" else count > 0
    if required:
        return any(
            type(n).__name__ == required
            or isinstance(n, ast.Attribute) and n.attr == required
            or isinstance(n, ast.Name) and n.id == required
            for n in ast.walk(tree)
        )
    return True


def check_call_keywords(tree, rule):
    """Check named reduction options, including literal variables and **dicts."""
    bindings = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            bindings.update((t.id, stmt.value) for t in targets if isinstance(t, ast.Name))

    def literal(node, seen=frozenset()):
        if isinstance(node, ast.Name) and node.id in bindings and node.id not in seen:
            return literal(bindings[node.id], seen | {node.id})
        return ast.literal_eval(node)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if rule.get("name") is not None and not (
                isinstance(fn, ast.Name) and fn.id == rule["name"]
                or isinstance(fn, ast.Attribute) and fn.attr == rule["name"]):
            continue
        options = {}
        for keyword in node.keywords:
            try:
                value = literal(keyword.value)
                if keyword.arg is None:
                    if isinstance(value, dict):
                        options.update(value)
                else:
                    options[keyword.arg] = value
            except (ValueError, TypeError, SyntaxError):
                continue
        if all(key in options and isinstance(options[key], bool) == isinstance(value, bool)
               and options[key] == value
               for key, value in rule["keywords"].items()):
            return True
    return False


def check_argument_syntax(tree, rule):
    name = rule["name"]
    if "variadic" in rule:
        definition = next(
            (stmt for stmt in reversed(tree.body)
             if isinstance(stmt, ast.FunctionDef) and stmt.name == name),
            None,
        )
        if definition is None:
            return False
        args = definition.args
        if [bool(args.vararg), bool(args.kwarg)] != rule["variadic"]:
            return False
        if not rule["forward"]:
            return True
        positional = args.posonlyargs + args.args
        if not positional:
            return False
        name = positional[0].arg
        scope = definition.body
        roots = [node.value for node in ast.walk(definition)
                 if isinstance(node, ast.Return) and node.value is not None]
    else:
        if any(isinstance(stmt, (ast.FunctionDef, ast.ClassDef)) and stmt.name == name
               for stmt in tree.body):
            return False
        scope = tree.body
        roots = [ast.Name(id="result")]

    bindings = {}
    for stmt in scope:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            bindings.update((target.id, stmt.value) for target in targets
                            if isinstance(target, ast.Name))

    def callee(expr):
        seen = set()
        while isinstance(expr, ast.Name) and expr.id in bindings and expr.id not in seen:
            seen.add(expr.id)
            expr = bindings[expr.id]
        return isinstance(expr, ast.Name) and expr.id == name

    visited = set()
    while roots:
        node = roots.pop()
        if id(node) in visited:
            continue
        visited.add(id(node))
        roots.extend(ast.iter_child_nodes(node))
        if isinstance(node, ast.Name) and node.id in bindings:
            roots.append(bindings[node.id])
        if not isinstance(node, ast.Call) or not callee(node.func):
            continue
        stars = [isinstance(arg, ast.Starred) for arg in node.args]
        keys = [kw.arg for kw in node.keywords]
        if "forms" in rule:
            if not any(stars) and any(
                len(stars) == count and set(keys) == set(names)
                for count, names in rule["forms"]
            ):
                return True
        else:
            direct, expand_args, expand_kwargs = rule.get("unpack", [0, True, True])
            if (stars[:direct] == [False] * direct
                    and all(stars[direct:]) and bool(stars[direct:]) == expand_args
                    and all(key is None for key in keys) and bool(keys) == expand_kwargs):
                return True
    return False


def run_browser_payload(payload, required):
    data = json.loads(payload)
    started = time.perf_counter()
    static_ok, reusable = True, True
    try:
        tree = ast.parse(data["code"])
        # Fixture Path inputs are supplied afresh for every case. Only direct
        # trusted Path assignments are inferred; unfamiliar setups stay cold.
        path_inputs = None
        for case in data["cases"]:
            fixture_paths = {
                target.id for stmt in ast.parse(case["setup"]).body
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == "Path"
                for target in stmt.targets if isinstance(target, ast.Name)
            }
            # Some file fixtures assign Path(...) / "file" rather than Path(...).
            path_inputs = fixture_paths if path_inputs is None else path_inputs & fixture_paths
        reusable = reusable_browser_code(tree, path_inputs or ())
        static_ok = check_syntax(tree, required)
    except SyntaxError:
        static_ok = False
    checks_ms = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    timings = {}
    clock, dump = time.perf_counter, json.dumps
    result = run_payload(data, timings)
    timings["cases_ms"] = (clock() - started) * 1000
    timings["checks_ms"] = checks_ms
    result.update(static_ok=static_ok, retire=not reusable, timings=timings)
    return dump(result, ensure_ascii=False, allow_nan=False)


if __name__ == "__main__":
    import sys

    payload = json.loads(sys.stdin.read(1000000))
    print(json.dumps(run_payload(payload), ensure_ascii=False, allow_nan=False))
