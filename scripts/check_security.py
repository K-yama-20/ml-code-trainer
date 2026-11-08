"""Fail closed on accidental public private-content copies or unsafe settings."""

from pathlib import Path
import json
import ast

ROOT = Path(__file__).resolve().parents[1]
public = json.loads((ROOT / "content/compiled/public.json").read_text(encoding="utf-8"))
for p in public["problems"]:
    assert not {"hidden_tests", "solution", "hints"} & p.keys(), p["id"]
for file in (ROOT / "apps/web/src").rglob("*"):
    if file.is_file() and ".test." not in file.name:
        source = file.read_text(encoding="utf-8")
        assert "MODAL_TOKEN_SECRET" not in source
        assert "SUPABASE_SERVICE_ROLE" not in source
        assert "compiled/private" not in source
        assert "compiled/variant-99" not in source
tree = ast.parse((ROOT / "apps/api/app/main.py").read_text(encoding="utf-8"))
assert not any(
    isinstance(n, ast.Call)
    and isinstance(n.func, ast.Name)
    and n.func.id in ("exec", "eval")
    for n in ast.walk(tree)
)
source = (ROOT / "apps/api/app/execution.py").read_text(encoding="utf-8")
assert "block_network=True" in source and "secrets=[]" in source
assert "runuser" in source and "learner" in source
print(
    "Security invariants passed: private content, server exec boundary, secrets, network isolation"
)
