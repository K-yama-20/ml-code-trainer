import pytest
from apps.api.app.grading import equivalent, judge, static_check
from content.runner import run_payload


@pytest.mark.parametrize(
    "body", ["return x.mean(axis=1)", "return np.mean(x,axis=1)", "return np.sum(x,axis=1)/x.shape[1]"]
)
def test_multiple_correct_solutions(body):
    case = {
        "setup": "import numpy as np\nx=np.array([[1.,3.],[2.,6.]])",
        "args": "x",
        "expected": {"kind": "array", "shape": [2], "dtype": "float64", "data": [2.0, 4.0]},
    }
    code = "def solve(x):\n    " + body
    output = run_payload({"code": code, "cases": [case]})
    assert judge(output["outputs"], [case], code)["verdict"] == "Accepted"


def test_syntax_runtime_nan_dtype_and_shape():
    case = {"expected": 1}
    assert judge([], [case], "def solve(:")["verdict"] == "Syntax Error"
    assert (
        judge([{"error": "name missing", "kind": "NameError"}], [case], "def solve(): pass")["verdict"]
        == "Runtime Error"
    )
    assert equivalent(
        {"data": ["__NaN__", "__Inf__"], "shape": [2], "dtype": "float32"},
        {"data": ["__NaN__", "__Inf__"], "shape": [2], "dtype": "float64"},
    )
    assert not equivalent({"shape": [1, 2]}, {"shape": [2]})
    assert not equivalent({"dtype": "int64"}, {"dtype": "float32"}, check_dtype=True)
    assert not equivalent(True, 1)
    assert not equivalent(0, False)


def test_ast_is_not_comment_matching():
    assert not static_check("# np.mean\ndef solve(x): return x", "mean")
    assert static_check("def solve(x): return x.mean()", "mean")
    assert not static_check("def solve(x): return 'mean'", "mean")
    assert static_check("result = x.shape", "attr:shape")
    assert not static_check("shape = (0, 4)\nresult = shape", "attr:shape")
    assert static_check("infer = -1\nresult = x.reshape(infer, width)", "literal:-1")
    assert not static_check("result = x.reshape(2, width) # -1", "literal:-1")
    assert not static_check("result = x.reshape(-10)", "literal:-1")
    assert not static_check("result = x.shape[-1]", "not:literal:-1")
    assert static_check("result = x.shape[2]", "not:literal:-1")
    assert static_check("result = np.moveaxis(x, (0, 4), (1, 2))", "call-count:moveaxis:1")
    assert not static_check(
        "result = np.moveaxis(np.moveaxis(x, 0, 1), -1, 2)",
        "call-count:moveaxis:1",
    )
    assert not static_check("# np.moveaxis(x, 0, 1)\nresult = x", "call-count:moveaxis:1")


def test_reduction_keyword_conditions_are_attached_to_the_requested_call():
    rule = 'call-keywords:{"name":"sum","keywords":{"keepdims":true}}'
    assert static_check("result = x.sum(axis=0, keepdims=True)", rule)
    assert static_check("keep = True\nresult = np.sum(x, axis=0, keepdims=keep)", rule)
    assert static_check("opts = {'keepdims': True}\nresult = np.sum(x, **opts)", rule)
    assert not static_check("result = np.sum(x) # keepdims=True", rule)
    assert not static_check("result = np.mean(x, keepdims=True)", rule)
    assert not static_check("result = np.sum(x, keepdims=False)", rule)


def test_numeric_scalar_contract_rejects_zero_dimensional_arrays_and_bools():
    from content.runner import wrong_result_type
    import numpy as np

    for value in (0, 2.5, np.int64(3), np.float32(0.5)):
        assert not wrong_result_type(value, "number")
    for value in (True, np.bool_(False), np.array(3), [3]):
        assert wrong_result_type(value, "number")


def test_comparison_details_never_contain_hidden_values():
    cases=[{"expected":1},{"expected":{"secret":"hidden value"}}]
    result=judge([{"value":2},{"value":{"secret":"hidden value"}}],cases,"pass",public_count=1)
    assert result["tests"][0]["actual"]==2 and result["tests"][0]["expected"]==1
    assert "actual" not in result["tests"][1] and "expected" not in result["tests"][1]


def test_side_effects_and_extra_dictionary_keys_are_rejected():
    case = {
        "setup": "import numpy as np\nx=np.array([1.,2.])",
        "args": "x",
        "expected": {"kind": "array", "shape": [2], "dtype": "float64", "data": [1.0, 2.0]},
    }
    code = "def solve(x):\n    x *= 2\n    return x / 2\n"
    output = run_payload({"code": code, "cases": [case]})
    assert output["outputs"][0]["mutated_inputs"] is True
    assert judge(output["outputs"], [case], code, protect_inputs=True)["verdict"] == "Wrong Answer"
    assert not equivalent({"a": 1, "extra": 2}, {"a": 1})


def test_scalar_array_contract_preserves_shape_without_changing_legacy_packing():
    case = {
        "setup": "import numpy as np\nx = np.array([[[9]]])",
        "args": "x",
    }
    script = {"mode": "script", "inputs": ["x"], "globals": ["np"]}
    payload = {"code": "result = np.squeeze(x)", "cases": [case], "execution": script}
    assert run_payload(payload)["outputs"][0]["value"] == 9
    script["result_type"] = "array"
    output = run_payload(payload)["outputs"][0]
    assert output["value"] == {"kind": "array", "shape": [], "dtype": "int64", "data": 9}
    assert not output.get("wrong_type")
    payload["code"] = "result = np.squeeze(x).item()"
    assert run_payload(payload)["outputs"][0]["wrong_type"]
