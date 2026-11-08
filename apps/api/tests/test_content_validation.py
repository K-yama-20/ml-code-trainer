import ast

import pytest

from content.runner import reusable_browser_code
from scripts.validate_content import check_python


@pytest.mark.parametrize("symbol", ["≠", "＝", "×", "÷", "−", "＂"])
def test_code_rejects_invalid_operators_but_allows_them_in_text(symbol):
    with pytest.raises(ValueError, match="invalid Python operator"):
        check_python(f"result = 1 {symbol} 2", "example")
    check_python(f"result = {symbol!r} # {symbol}", "example")


@pytest.mark.parametrize("code", [
    "result = dict(zip(keys, values))",
    "result = x.mean(axis=1)",
    "import numpy as np\nresult = np.where(x < 0, 0, x)",
    "result = df.loc[df['score'] >= 5]",
    "result = json.loads(text)",
    "import json as j\nresult = j.dumps(config, ensure_ascii=False)",
    "from pathlib import Path\nresult = Path(path).name",
    "result = Path(path).stem",
    'path = Path("a.csv")\nresult = path.with_suffix(".json")',
    'p = Path(path)\nresult = p.parent / f"{p.stem}_backup{p.suffix}"',
])
def test_fast_runtime_supports_common_exercises(code):
    assert reusable_browser_code(ast.parse(code))


@pytest.mark.parametrize("code", [
    "import sys\nsys.modules.clear()",
    "open('/tmp/cross-run', 'w')",
    "f = eval\nf('0')",
    "import numpy as np\nnp.seterr(all='ignore')",
    "import numpy as np\nnp.mean = sum",
    "result = np.empty_like(x)",
    "result = (1).__class__",
    "result = globals()",
    'path.write_text("changed")',
    'with path.open("a") as f:\n    f.write(text)',
    "result = other.loads(text)",
    "result = other.name",
    "json = other\nresult = json.loads(text)",
    "import json\njson.dumps = str",
])
def test_runtime_retires_after_stateful_or_reflective_python(code):
    assert not reusable_browser_code(ast.parse(code))


def test_trusted_fixture_paths_are_reused_without_running_the_fixture_in_the_check():
    from content.runner import run_browser_payload
    import json

    payload = json.dumps({
        "code": 'result = path.with_suffix(".json")',
        "execution": {"mode": "script", "inputs": ["path"], "globals": []},
        "cases": [{
            "setup": 'from pathlib import Path\npath = Path("outputs/data.csv")',
            "args": "path",
        }],
    })
    result = json.loads(run_browser_payload(payload, ""))
    assert result["retire"] is False
    assert result["outputs"][0]["value"]["value"] == "outputs/data.json"
