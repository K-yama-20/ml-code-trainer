"""PT10: saving and restoring state with state_dict and checkpoints.

Oracles read the fixture's parameters directly (before any save/load) and
compute outputs in NumPy, so a restore that silently fails is detected."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT10"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["model = nn.Sequential(nn.Linear(1, 1, bias=False), nn.ReLU(), nn.Linear(1, 2))", "model = nn.BatchNorm1d(3)"],
    2: ["values = [-0.5]", "values = [[1.0, 0.0], [0.0, 1.0]]"],
    3: ["weight = torch.tensor([[0.0, 0.0]])", "weight = torch.tensor([[-1.5, 3.0]])"],
    4: ["model = nn.Linear(4, 1, bias=False)", "model = nn.Sequential(nn.Linear(2, 3), nn.BatchNorm1d(3))"],
    5: ["model = nn.Linear(2, 1)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[0.0, 2.0]]))\n    model.bias.fill_(-1.0)\nx = torch.tensor([[5.0, 5.0]])",
        "model = nn.Linear(2, 1)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[1.0, 1.0]]))\n    model.bias.fill_(0.0)\nx = torch.tensor([[1.0, 2.0], [3.0, 4.0], [-1.0, 0.0]])"],
    6: ["step = 0\ntensor = torch.tensor([3.0])", "step = 120\ntensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]])"],
    7: ["model = nn.Linear(2, 1, bias=False)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[0.5, 0.5]]))",
        "model = nn.Linear(3, 1, bias=False)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[-1.0, 2.0, 0.0]]))"],
    8: ["model = nn.Linear(2, 1, bias=False)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[-3.0, 0.0]]))\nvalue = 5.0",
        "model = nn.Linear(1, 1, bias=False)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[4.0]]))\nvalue = -1.0"],
    9: ["model = nn.Linear(2, 1)\nstate = {}", "model = nn.Sequential(nn.Linear(1, 1), nn.Linear(1, 1))\nstate = {\"0.weight\": torch.zeros(1, 1), \"1.bias\": torch.zeros(1)}"],
    10: ["model = nn.Linear(2, 1)\nstate = {\"weight\": torch.zeros(1, 2), \"bias\": torch.zeros(1)}",
         "model = nn.Linear(1, 1, bias=False)\nstate = {\"weight\": torch.zeros(1, 1), \"extra\": torch.zeros(1), \"another\": torch.zeros(2)}"],
    11: ["w = nn.Parameter(torch.tensor([0.0]))\nlr = 0.5", "w = nn.Parameter(torch.tensor([[1.0, 1.0]]))\nlr = 0.001"],
    12: ["model = nn.Linear(1, 1)\nwith torch.no_grad():\n    model.weight.fill_(-1.0)\n    model.bias.fill_(2.0)\nepoch = 0",
         "model = nn.Linear(1, 1)\nwith torch.no_grad():\n    model.weight.fill_(0.25)\n    model.bias.fill_(0.0)\nepoch = 9"],
    13: ["model = nn.Sequential(nn.Linear(2, 1), nn.Dropout(0.5))\nwith torch.no_grad():\n    model[0].weight.copy_(torch.tensor([[0.0, -1.0]]))\n"
         "    model[0].bias.fill_(2.0)\nx = torch.tensor([[3.0, 3.0]])",
         "model = nn.Sequential(nn.Linear(2, 1), nn.Dropout(0.5))\nwith torch.no_grad():\n    model[0].weight.copy_(torch.tensor([[2.0, 2.0]]))\n"
         "    model[0].bias.fill_(0.0)\nx = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])"],
    14: ["tensor = torch.tensor([0.0])", "tensor = torch.arange(6.0).reshape(2, 3)"],
    15: ["model = nn.Sequential(nn.Linear(2, 2), nn.ReLU(), nn.Linear(2, 1))\nwith torch.no_grad():\n"
         "    model[0].weight.copy_(torch.tensor([[0.0, 1.0], [2.0, 0.0]]))\n    model[0].bias.copy_(torch.tensor([1.0, 1.0]))\n"
         "x = torch.tensor([[1.0, 1.0], [-1.0, 0.0]])",
         "model = nn.Sequential(nn.Linear(2, 2), nn.ReLU(), nn.Linear(2, 1))\nwith torch.no_grad():\n"
         "    model[0].weight.copy_(torch.tensor([[-1.0, 0.0], [0.0, -1.0]]))\n    model[0].bias.copy_(torch.tensor([0.0, 0.0]))\n"
         "x = torch.tensor([[4.0, -4.0]])"],
    16: ["state = {\"module.weight\": torch.tensor([[0.0, 1.0]]), \"module.bias\": torch.tensor([0.0])}",
         "state = {\"module.bias\": torch.tensor([-2.0]), \"module.weight\": torch.tensor([[3.0, 3.0]])}"],
    17: ["model = nn.BatchNorm1d(1)\nwith torch.no_grad():\n    model.running_mean.copy_(torch.tensor([5.0]))\n    model.running_var.copy_(torch.tensor([0.5]))",
         "model = nn.BatchNorm1d(3)\nwith torch.no_grad():\n    model.running_mean.copy_(torch.tensor([0.0, 1.0, 2.0]))\n"
         "    model.running_var.copy_(torch.tensor([1.0, 1.0, 2.0]))"],
    18: ["model = nn.Linear(2, 1)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[0.0, 0.0]]))\n    model.bias.fill_(1.0)\n"
         "x = torch.tensor([[1.0, -1.0], [3.0, 1.0]])",
         "model = nn.Linear(2, 1)\nwith torch.no_grad():\n    model.weight.copy_(torch.tensor([[2.0, -2.0]]))\n    model.bias.fill_(0.0)\n"
         "x = torch.tensor([[0.5, 0.5]])"],
}

_PRELUDE = """
import numpy as np
def _np(t):
    return np.asarray(t.tolist(), dtype=np.float64).reshape(tuple(t.shape))
def _f(a):
    return torch.from_numpy(np.array(a, dtype=np.float64, order="C")).to(torch.float32)
def _names(m):
    return [n for n, _ in m.named_parameters()] + [n for n, _ in m.named_buffers()]
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = sorted(_names(model))",
    2: "expected = _f(values)",
    3: "expected = _f(_np(weight))",
    4: "expected = {**{n: tuple(p.shape) for n, p in model.named_parameters()}, **{n: tuple(b.shape) for n, b in model.named_buffers()}}",
    5: "expected = _f(_np(x) @ _np(model.weight).T + _np(model.bias))",
    6: "expected = (step, tensor.clone())",
    7: "expected = _f(_np(model.weight))",
    8: "expected = (_f(_np(model.weight)), _f(np.full(tuple(model.weight.shape), value)))",
    9: "expected = sorted(set(_names(model)) - set(state))",
    10: "expected = sorted(set(state) - set(_names(model)))",
    11: "expected = lr",
    12: "expected = (epoch + 1, _f(_np(model.weight)))",
    13: "expected = (_f(_np(x) @ _np(model[0].weight).T + _np(model[0].bias)), False)",
    14: "expected = ('cpu', tensor.clone())",
    15: "expected = _f(_np(x) @ _np(model[0].weight).T + _np(model[0].bias))",
    16: "expected = _f(_np(state['module.weight']))",
    17: "expected = (_f(_np(model.running_mean)), _f(_np(model.running_var)))",
    18: ("_W = _np(model.weight)\n_g = _np(x).sum(axis=0, keepdims=True)\n"
         "expected = (_f(_W - 0.5 * _g), _f(_W))"),
}.items()}

RULES = {
    1: {"required": "call:state_dict"},
    2: {"required": 'all:["call:save", "call-keywords:{\\"name\\": \\"load\\", \\"keywords\\": {\\"weights_only\\": true}}"]'},
    3: {"required": "call:load_state_dict"},
    4: {"required": "call:state_dict"},
    5: {"required": 'all:["call:save", "call:load_state_dict"]'},
    6: {"required": 'all:["call:save", "call-keywords:{\\"name\\": \\"load\\", \\"keywords\\": {\\"weights_only\\": true}}"]'},
    7: {"required": "call:clone"},
    8: {"required": "call:clone"},
    9: {"required": "call-keywords:{\"name\": \"load_state_dict\", \"keywords\": {\"strict\": false}}"},
    10: {"required": "call-keywords:{\"name\": \"load_state_dict\", \"keywords\": {\"strict\": false}}"},
    11: {"required": "call:load_state_dict"},
    12: {"required": 'all:["call:save", "call:load_state_dict"]'},
    13: {"required": 'all:["call:load_state_dict", "call:eval"]'},
    14: {"required": "call-keywords:{\"name\": \"load\", \"keywords\": {\"map_location\": \"cpu\"}}"},
    15: {"required": "call:load_state_dict"},
    16: {"required": "call:load_state_dict"},
    17: {"required": "call:load_state_dict"},
    18: {"required": 'all:["call:save", "call:load_state_dict"]'},
}

WRONG = {
    1: ["result = sorted(n for n, _ in model.named_parameters())", "result = list(model.state_dict().keys())[::-1]"],
    2: ["with tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / \"weights.pt\"\n"
        "    torch.save({\"weight\": torch.tensor(values, dtype=torch.float64)}, path)\n"
        "    loaded = torch.load(path, weights_only=True, map_location=\"cpu\")\nresult = loaded[\"weight\"]"],
    3: ["model = nn.Linear(2, 1, bias=False)\nresult = model.weight.detach()"],
    4: ["result = {k: tuple(v.shape) for k, v in model.named_parameters()}"],
    5: ["restored = nn.Linear(2, 1)\nresult = restored(x)"],
    6: ["with tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / \"checkpoint.pt\"\n"
        "    torch.save({\"step\": step + 1, \"tensor\": tensor}, path)\n    data = torch.load(path, weights_only=True, map_location=\"cpu\")\n"
        "result = (data[\"step\"], data[\"tensor\"])"],
    7: ["saved = model.state_dict()\nwith torch.no_grad():\n    model.weight.zero_()\nresult = saved[\"weight\"]"],
    8: ["shared = model.state_dict()\ncopied = {k: v.clone() for k, v in model.state_dict().items()}\nwith torch.no_grad():\n"
        "    model.weight.fill_(value)\nresult = (shared[\"weight\"], copied[\"weight\"])"],
    9: ["outcome = model.load_state_dict(state, strict=False)\nresult = sorted(outcome.unexpected_keys)"],
    10: ["outcome = model.load_state_dict(state, strict=False)\nresult = sorted(outcome.missing_keys)"],
    11: ["restored = torch.optim.SGD([w], lr=1.0)\nresult = restored.param_groups[0][\"lr\"]"],
    12: ["with tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / \"checkpoint.pt\"\n"
         "    torch.save({\"model\": model.state_dict(), \"epoch\": epoch}, path)\n    checkpoint = torch.load(path, weights_only=True)\n"
         "restored = nn.Linear(1, 1)\nrestored.load_state_dict(checkpoint[\"model\"])\nresult = (checkpoint[\"epoch\"], restored.weight.detach())"],
    13: ["restored = nn.Sequential(nn.Linear(2, 1), nn.Dropout(0.5))\nrestored.load_state_dict(model.state_dict())\nrestored.eval()\n"
         "with torch.no_grad():\n    out = restored(x)\nrestored.train()\nresult = (out, restored.training)"],
    14: ["with tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / \"tensor.pt\"\n    torch.save(tensor, path)\n"
         "    loaded = torch.load(path, map_location=\"cpu\", weights_only=True)\nresult = (loaded.device, loaded)"],
    15: ["result = model(x)"],
    16: ["model = nn.Linear(2, 1)\nmodel.load_state_dict(state, strict=False)\nresult = model.weight.detach()"],
    17: ["restored = nn.BatchNorm1d(model.num_features)\nresult = (restored.running_mean, restored.running_var)"],
    18: ["with tempfile.TemporaryDirectory() as directory:\n    path = Path(directory) / \"best.pt\"\n"
         "    optimizer = torch.optim.SGD(model.parameters(), lr=0.5)\n    optimizer.zero_grad()\n    model(x).sum().backward()\n"
         "    optimizer.step()\n    torch.save(model.state_dict(), path)\n    updated = model.weight.detach().clone()\n"
         "    model.load_state_dict(torch.load(path, weights_only=True))\nresult = (updated, model.weight.detach().clone())"],
}


def compile_checkpoints(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
