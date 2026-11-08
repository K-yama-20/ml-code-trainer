"""Versioned concrete-input workspaces, compiled from the trusted curriculum AST.

This changes the answer interface, not the oracle or the underlying objectives.
The caller's fixtures stay private; only a materialized public example is shown.
"""

import ast
import inspect
import math

from content.catalog import PRELUDE, TORCH_PRELUDE

PILOT = {
    "PY01-01",
    "PY02-06",
    "PY03-04",
    "NP05-01",
    "NP05-03",
    "NP05-05",
    "NP06-04",
    "PD01-01",
    "PD02-04",
    "PD04-06",
    "SK02-04",
    "SK03-05",
    "PT02-02",
    "PT05-03",
    "PT07-04",
}

# These four tasks explicitly teach signatures, defaults, *args, or **kwargs.
FUNCTIONS = {
    "PY02-01": "scale_values",
    "PY02-03": "read_learning_rate",
    "PY02-05": "total_with_offset",
    "PY02-06": "apply_config",
}


def literal(value):
    module = type(value).__module__.split(".")[0]
    if module == "numpy":
        if not hasattr(value, "ndim") or value.ndim == 0:
            return literal(value.item())
        # Keep long regular training arrays readable, without changing any values.
        flat = value.ravel()
        if flat.size > 16 and flat.size > 1 and (flat[1:] - flat[:-1] == 1).all():
            return f"np.arange({literal(flat[0])}, {literal(flat[-1] + 1)}, dtype=np.{value.dtype}).reshape({value.shape!r})"
        return f"np.array({literal(value.tolist())}, dtype=np.{value.dtype}).reshape({value.shape!r})"
    if module == "torch":
        if not value.is_contiguous():
            raise ValueError(
                "Non-contiguous inputs must retain their original construction expression"
            )
        grad = ", requires_grad=True" if value.requires_grad else ""
        return f"torch.tensor({literal(value.tolist())}, dtype={value.dtype}{grad})"
    if module == "pandas":
        if value.ndim == 2:
            return f"pd.DataFrame({literal(value.to_numpy().tolist())}, columns={literal(value.columns.tolist())}, index={literal(value.index.tolist())})"
        return f"pd.Series({literal(value.tolist())}, index={literal(value.index.tolist())}, dtype={str(value.dtype)!r})"
    if isinstance(value, float) and not math.isfinite(value):
        return "float('nan')" if math.isnan(value) else f"float({str(value)!r})"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k!r}: {literal(v)}" for k, v in value.items()) + "}"
    if isinstance(value, (tuple, list)):
        parts = ", ".join(literal(v) for v in value)
        return (
            "(" + parts + ("," if len(value) == 1 else "") + ")"
            if isinstance(value, tuple)
            else "[" + parts + "]"
        )
    return repr(value)


def script(source):
    """Remove only the exercise wrapper; preserve nested functions and methods."""
    fn = ast.parse(source).body[0]
    assert isinstance(fn, ast.FunctionDef)

    class Returns(ast.NodeTransformer):
        def visit_Return(self, node):
            return ast.copy_location(
                ast.Assign(
                    [ast.Name("result", ast.Store())], node.value or ast.Constant(None)
                ),
                node,
            )

        def visit_FunctionDef(self, node):
            return node

        visit_ClassDef = visit_FunctionDef
        visit_AsyncFunctionDef = visit_FunctionDef

    body = [Returns().visit(node) for node in fn.body]
    return (
        ast.unparse(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])))
        + "\n"
    )


def bindings(p, case):
    env = {"seed": p["variant_seed"]}
    exec(case["setup"], env)
    exec(p["solution"], env)
    args, kwargs = eval(
        "_capture(" + case["args"] + ")", env, {"_capture": lambda *a, **kw: (a, kw)}
    )
    sig = inspect.signature(env["solve"])
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    call = ast.parse("_capture(" + case["args"] + ")").body[0].value
    expressions = dict(zip(sig.parameters, call.args))
    expressions.update({k.arg: k.value for k in call.keywords if k.arg})
    lines = []
    imports = PRELUDE + (TORCH_PRELUDE if p["module_id"] == "pytorch" else "")
    global_names = set()
    for node in ast.parse(imports).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            global_names.update(
                alias.asname or alias.name.split(".")[0] for alias in node.names
            )
    for name, value in bound.arguments.items():
        expr = expressions.get(name)
        # Preserve layout/grad/dtype construction, e.g. torch.arange(...).T.
        safe = expr is not None and all(
            n.id in global_names or n.id in {"True", "False", "None"}
            for n in ast.walk(expr)
            if isinstance(n, ast.Name)
        )
        if sig.parameters[name].kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            safe = False
        code = ast.unparse(expr) if safe else literal(value)
        if (
            safe
            and expr is not None
            and isinstance(expr, ast.Call)
            and isinstance(expr.func, ast.Attribute)
            and expr.func.attr in ("array", "tensor")
            and expr.args
            and isinstance(expr.args[0], ast.List)
            and expr.args[0].elts
            and all(isinstance(v, ast.List) for v in expr.args[0].elts)
            and not expr.keywords
        ):
            rows = ",\n".join("    " + ast.unparse(row) for row in expr.args[0].elts)
            code = ast.unparse(expr.func) + "([\n" + rows + "\n])"
        lines.append(f"{name} = {code}")
    needed = set()
    for source in (
        "\n".join(lines),
        script(p["solution"]),
        p["example"] if p["type"] == "prediction" else "",
    ):
        needed.update(
            n.id for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Name)
        )
    import_lines = []
    for node in ast.parse(imports).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            aliases = [
                a for a in node.names if (a.asname or a.name.split(".")[0]) in needed
            ]
            if aliases:
                node.names = aliases
                import_lines.append(ast.unparse(node))
    return (
        "\n".join(import_lines) + ("\n\n" if import_lines else "") + "\n".join(lines),
        list(bound.arguments),
        sorted(global_names),
        sig,
    )


def task(p):
    # Keep the task's domain conditions; remove only the old interface preamble.
    text = p["description"].split("\n\n")[-1]
    if p["id"] == "PY02-06":
        return "apply_configの中にapply(values, factor=1)を定義してください。applyは各値をfactor倍したリストを返します。最後にapply(**config)の結果を返してください。"
    if p["id"] in FUNCTIONS:
        return text + f" 関数{FUNCTIONS[p['id']]}を完成させてください。"
    if p["type"] == "prediction":
        return "表示されたコードを読み、observedに入る値を答えてください。コードの実装は不要です。"
    return (
        text.removesuffix("返してください。") + "resultに代入してください。"
        if text.endswith("返してください。")
        else text + " 処理の結果をresultに代入してください。"
    )


def improve_concrete(p, make_case, exercise, module, effective_seed):
    pid = p["id"]
    # Small, authored examples. Other cases still exercise different values/shapes.
    displays = {
        "PY01-01": "[-2,0,3]",
        "NP05-01": "np.array([[1.,4.,5.],[2.,10.,-4.]])",
        "NP05-03": "np.array([[1.,2.],[3.,4.],[5.,6.]])",
        "NP05-05": "np.arange(16.).reshape(2,2,2,2)",
        "SK02-04": "np.array([[0.,2.],[2.,4.],[4.,6.]]), np.array([[100.,102.]])",
    }
    if pid in displays:
        p["public_tests"][0] = make_case(
            exercise, module, displays[pid], effective_seed
        )
    provided, inputs, globals_, sig = bindings(p, p["public_tests"][0])
    mode = (
        "prediction"
        if p["type"] == "prediction"
        else "function"
        if pid in FUNCTIONS
        else "script"
    )
    model = p["solution"]
    has_class = any(isinstance(n, ast.ClassDef) for n in ast.walk(ast.parse(model)))
    if mode == "script":
        p["solution"] = script(model)
        if p["type"] == "bugfix" or p["stage"] == "guided":
            p["starter_code"] = script(p["starter_code"])
        else:
            p["starter_code"] = (
                "result =\n"
                if p["stage"] == "partial"
                else "# ここに処理を書き、resultに代入してください\n"
            )
        p["execution"] = {
            "mode": "script",
            "inputs": inputs,
            "globals": globals_,
            "allow_input_mutation": not p["protect_inputs"],
        }
        # Literal answers are legitimate only in prediction tasks. Constant-output
        # API exercises also require the existing pedagogical API/AST condition.
        expected = [c["expected"] for c in p["public_tests"] + p["hidden_tests"]]
        if all(v == expected[0] for v in expected) and p["required_ast"]:
            p["execution"]["constant_goal"] = True
        if p["required_ast"] and p["required_ast"] not in ("ClassDef", "With", "iloc"):
            p["required_ast"] = "call:" + p["required_ast"]
    elif mode == "function":
        entry = FUNCTIONS[pid]
        for field in ("starter_code", "solution"):
            node = ast.parse(p[field])
            node.body[0].name = entry
            p[field] = ast.unparse(node) + "\n"
        p["execution"] = {"mode": "function", "entrypoint": entry}
    else:
        p["public_tests"] = p["public_tests"][:1]
        p["hidden_tests"] = []
        # The observation is a single concrete program, not a hidden function of inputs.
        observation = ast.parse(p["example"])
        observation.body = [
            n
            for n in observation.body
            if not isinstance(n, ast.Assign)
            or not any(isinstance(t, ast.Name) and t.id in inputs for t in n.targets)
        ]
        provided += "\n\n" + ast.unparse(observation)
        p["presentation"] = p.get("presentation") or {}
        first = p["public_tests"][0]["expected"]
        p["presentation"]["answer"] = {
            "mode": "fixed",
            "wrap_array": isinstance(first, dict) and first.get("kind") == "array",
        }

    guide = (
        "observedに入る値を入力してください。"
        if mode == "prediction"
        else "強調された空欄だけを埋めてください。入力データは編集できません。"
        if p["stage"] == "guided" and p["starter_code"].count("___") == 1
        else "表示された不具合のある処理を修正してください。入力データはそのまま使います。"
        if p["type"] == "bugfix"
        else f"{FUNCTIONS[pid]}の処理を完成させてください。下に使用例があります。"
        if mode == "function"
        else "resultの右側に処理を書いてください。複数行で書いても構いません。"
        if p["stage"] == "partial"
        else "必要な処理を書き、結果をresultに代入してください。"
    )
    presentation = p.get("presentation") or {}
    presentation.update(edit_instruction=guide)
    presentation.setdefault("worked_example", "")
    presentation.setdefault(
        "feedback",
        {
            "wrong": "入力の各値を使って計算できているか、resultの値と形を動作確認で比べてください。",
            "runtime": "示されたエラーの行を確認してください。入力を初期化し直さず、解答部分だけを書きます。",
        },
    )
    p["presentation"] = presentation
    p["workspace"] = {
        "mode": mode,
        "provided_code": provided,
        "task": task(p),
        "authored": pid in PILOT,
        "structure": "class" if has_class else mode,
    }
    if mode == "function":
        params = []
        for name, param in sig.parameters.items():
            params.append(
                (
                    "*"
                    if param.kind == inspect.Parameter.VAR_POSITIONAL
                    else "**"
                    if param.kind == inspect.Parameter.VAR_KEYWORD
                    else f"{name}="
                    if param.kind == inspect.Parameter.KEYWORD_ONLY
                    else ""
                )
                + name
            )
        p["workspace"]["invocation"] = f"result = {FUNCTIONS[pid]}({', '.join(params)})"
    p["input_conditions"] = (
        "入力データは解答欄の上に用意されています。採点では値や大きさを変えて同じ処理を確認します。"
        if mode != "prediction"
        else "表示されたデータについてのみ予測します。"
    )
    if mode == "script":
        p["hints"] = p["hints"][:2] + ["解答部分は次の形で書けます。\n" + p["solution"]]
    if (
        mode != "prediction"
        and p["stage"] == "guided"
        and p["starter_code"].count("___") == 1
    ):
        prefix, suffix = p["starter_code"].split("___")
        if p["solution"].startswith(prefix) and p["solution"].endswith(suffix):
            answer = p["solution"][
                len(prefix) : len(p["solution"]) - len(suffix) if suffix else None
            ]
            p["hints"][2] = (
                f"空欄には {answer} と入力します。周囲のコードと合わせて読んでみましょう。"
            )
    p["content_version"] += 1
    p["version_id"] = f"{pid}@{p['content_version']}"
    p["workspace"]["classification_reason"] = (
        "引数・既定値・展開の理解が目的のため関数を維持"
        if mode == "function"
        else "表示された固定コードの観察。数値・shape・値の専用回答欄"
        if mode == "prediction"
        else "クラスとforwardを維持し、採点用だけの外側のsolveを除去"
        if has_class
        else "ライブラリ操作の理解が目的。入力を固定表示し処理のみ記述"
    )
    if pid in PILOT:
        from content.concrete_lessons import refine

        refine(p)
    if pid == "PY02-01":
        p["content_version"] += 1
        p["version_id"] = f"{pid}@{p['content_version']}"
        p["workspace"]["provided_code"] = "x = [1, 2]"
        p["workspace"]["invocation"] = "result = scale_values(x)"
        p["workspace"]["task"] = "xの各値をscale倍したリストを返してください。scaleを省略すると2倍になります。"
        p["description"] = p["output_conditions"] = p["workspace"]["task"]
        p["hints"][1] = "関数の中ではscaleを使います。呼び出し側がscaleを省略すると、引数の既定値2が入ります。"
        p["explanation"] = "scale_values([1, 2])ではscaleが省略されるため、[2, 4]を返します。scale_values([1, 2], 3)なら[3, 6]です。"
        p["public_tests"][1] = make_case(exercise, module, "[1,2],3", effective_seed)
    refinements = {
        "PY02-02": ("可変長引数を読む", "totalを呼び出したとき、observedに入る値を答えてください。"),
        "NP03-02": ("expand_dims後のshape", "先頭に軸を足した配列のshapeを答えてください。"),
        "NP08-02": ("値を0から1に収める", "xの各値が0未満なら0、1より大きければ1に置き換えてください。np.clipの結果はresultに入ります。"),
        "NP09-02": ("softmaxの出力shape", "行ごとにsoftmaxを適用した後のshapeをタプルでresultに代入してください。softmax自体は計算不要です。"),
        "PD03-02": ("グループごとの全行数", "groupごとの行数を数え、Seriesをresultに代入してください。valueが欠損した行も数えます。"),
        "SK02-02": ("学習済みのScalerでテストを変換", "trainで学習済みのsを使ってtestを変換し、resultに代入してください。testで学習し直さないでください。"),
        "SK03-02": ("学習済みのモデルでラベルを予測", "学習済みのmを使ってXのラベルを予測し、resultに代入してください。"),
        "PT05-03": ("forwardで入力を2倍にする", "forwardで、受け取ったxを2倍したTensorを返してください。"),
    }
    if pid in refinements:
        p["content_version"] += 1
        p["version_id"] = f"{pid}@{p['content_version']}"
        p["title"], description = refinements[pid]
        p["workspace"]["task"] = p["description"] = p["output_conditions"] = description
    if pid == "PY02-02":
        call = p["public_tests"][0]["args"]
        p["workspace"]["provided_code"] = f"def total(*values):\n    return sum(values)\n\nobserved = total({call})"
        p["hints"][1] = "位置引数はすべてタプルvaluesに入り、sumがその合計を返します。"
    if pid == "PT05-03":
        p["starter_code"] = "class Twice(nn.Module):\n    def forward(self, x):\n        pass\n\nresult = Twice()(x)\n"
    if pid == "SK01-01":
        p["content_version"] += 1
        p["version_id"] = f"{pid}@{p['content_version']}"
        p["solution"] = p["starter_code"].replace("___", "(len(X_train), len(X_test))")
    if pid == "NP09-06":
        p["content_version"] += 1
        p["version_id"] = f"{pid}@{p['content_version']}"
    if pid == "NP05-05":
        p["content_version"] += 1
        p["version_id"] = f"{pid}@{p['content_version']}"
    if pid == "PY01-03":
        p["content_version"] += 1
        p["version_id"] = f"{pid}@{p['content_version']}"
        p["title"] = "zipで辞書を作る"
        p["description"] = p["workspace"]["task"] = "配列keysをキーに、valuesを値にした辞書をresultに代入してください。長さが異なるときは、短い側に合わせます。"
        p["hints"][1] = "zip(keys, values)で組を作り、dict()で辞書に変換できます。"
        p["public_tests"][0] = make_case(exercise, module, "['a','b'],[2,3]", effective_seed)
        p["workspace"]["provided_code"] = "keys = ['a', 'b']\nvalues = [2, 3]"
    return p
