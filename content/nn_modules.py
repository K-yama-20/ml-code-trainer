"""PT05: nn.Module structure, registration and forward.

Oracles derive counts and shapes from the layer sizes, and compute forward
passes in NumPy from the given weights."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT05"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["n = 0\nd = 2\nout = 1", "n = 4\nd = 5\nout = 2"],
    2: ["d = 1\nout = 1", "d = 5\nout = 4"],
    3: ["d = 1\nout = 1", "d = 4\nout = 3"],
    4: ["x = torch.zeros(2, 2)", "x = torch.tensor(-1.5)"],
    5: ["model = nn.Sequential(nn.Linear(2, 2, bias=False), nn.Tanh(), nn.Linear(2, 1))",
        "model = nn.Sequential(nn.ReLU(), nn.Linear(3, 3), nn.Dropout(0.1), nn.Linear(3, 2), nn.Linear(2, 1, bias=False))"],
    6: ["d = 3\nout = 2\nbias = True", "d = 1\nout = 5\nbias = False"],
    7: ["values = [0.5]\noffsets = [1.0, 2.0, 3.0]", "values = [[1.0, 2.0], [3.0, 4.0]]\noffsets = [0.0]"],
    8: ["weight = torch.tensor([[1.0, 1.0]])\nx = torch.tensor([[-1.0, 5.0]])",
        "weight = torch.tensor([[0.5, 0.0]])\nx = torch.tensor([[2.0, 9.0], [4.0, -9.0], [0.0, 0.0]])"],
    9: ["x = torch.zeros(1, 3)", "x = torch.ones(2, 4, 3)"],
    10: ["weight = torch.tensor([[1.0, 0.0], [0.0, 1.0]])\nbias = torch.tensor([-1.0, 1.0])\nx = torch.tensor([[0.5, -3.0]])",
         "weight = torch.tensor([[-1.0, -1.0], [2.0, 0.0]])\nbias = torch.tensor([0.0, 0.0])\nx = torch.tensor([[1.0, 1.0], [-1.0, -1.0], [3.0, 0.0]])"],
    11: ["model = nn.Sequential(nn.Linear(2, 2), nn.ReLU(), nn.Linear(2, 5), nn.Linear(5, 1))",
         "model = nn.Sequential(nn.Linear(10, 1), nn.Sigmoid())"],
    12: ["d = 1\nout = 1", "d = 4\nout = 3"],
    13: ["n = 1\nd = 4", "n = 5\nd = 1"],
    14: ["weight = torch.tensor([[1.0, 0.0], [0.0, 1.0]])\nbias = torch.tensor([0.0, 0.0])\nx = torch.tensor([[3.0, -1.0], [0.0, 2.0]])",
         "weight = torch.tensor([[-1.0, 0.0], [0.0, -1.0]])\nbias = torch.tensor([1.0, 1.0])\nx = torch.tensor([[5.0, 6.0]])"],
    15: ["model = nn.Sequential(nn.Linear(2, 1))\nvalue = -1.0\nx = torch.tensor([[1.0, 1.0], [2.0, 0.0]])",
         "model = nn.Sequential(nn.Linear(3, 2), nn.ReLU(), nn.Linear(2, 2), nn.ReLU(), nn.Linear(2, 1))\nvalue = 0.25\n"
         "x = torch.tensor([[1.0, 2.0, 3.0]])"],
    16: ["model = nn.Sequential(nn.Conv2d(1, 2, 3), nn.Flatten())",
         "model = nn.Sequential(nn.Linear(3, 3), nn.Tanh(), nn.Linear(3, 1), nn.Sigmoid(), nn.Identity())"],
    17: ["factor = -2.0\nx = torch.tensor([[1.0, 2.0]])", "factor = 0.5\nx = torch.tensor(4.0)"],
    18: ["d = 1\nh = 2", "d = 8\nh = 4"],
}

_PRELUDE = """
import numpy as np
def _np(t):
    return np.asarray(t.tolist(), dtype=np.float64).reshape(tuple(t.shape))
def _f(a):
    return torch.from_numpy(np.array(a, dtype=np.float64, order="C")).to(torch.float32)
def _linear_size(m):
    return m.in_features * m.out_features + (m.out_features if m.bias is not None else 0)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = (n, out)",
    2: "expected = (out, d)",
    3: "expected = d * out + out",
    4: "expected = _f(_np(x) * 2)",
    5: ("expected = []\nfor i, m in enumerate(model):\n    if isinstance(m, nn.Linear):\n"
        "        expected.append(f'{i}.weight')\n        if m.bias is not None:\n            expected.append(f'{i}.bias')"),
    6: "expected = 2 if bias else 1",
    7: "expected = int(np.asarray(values).size)",
    8: "expected = _f(_np(x) @ _np(weight).T)",
    9: "expected = (*tuple(x.shape[:-1]), 2)",
    10: "expected = _f(np.maximum(_np(x) @ _np(weight).T + _np(bias), 0))",
    11: "expected = sum(_linear_size(m) for m in list(model)[1:] if isinstance(m, nn.Linear))",
    12: "expected = {'fc.weight': (out, d), 'fc.bias': (out,), 'running': (out,)}",
    13: "expected = n * (d * d + d)",
    14: "expected = _f(_np(x) + _np(x) @ _np(weight).T + _np(bias))",
    15: ("_h = _np(x)\nfor m in model:\n    if isinstance(m, nn.Linear):\n"
         "        _h = _h @ np.full((m.out_features, m.in_features), value).T\n    else:\n        _h = np.maximum(_h, 0)\n"
         "expected = _f(_h)"),
    16: "expected = [m.__class__.__name__ for m in model]",
    17: "expected = _f(_np(x) * factor)",
    18: "expected = (h, d)",
}.items()}

RULES = {
    1: {"required": "call:Linear"},
    2: {"required": "call:Linear"},
    3: {"required": "ClassDef"},
    4: {"required": "ClassDef"},
    5: {"required": "call:named_parameters"},
    7: {"required": 'all:["ClassDef", "call:Parameter"]'},
    8: {"required": 'all:["call:Linear", "call:no_grad"]'},
    9: {"required": "call:Sequential"},
    10: {"required": "ClassDef"},
    12: {"required": "call:register_buffer"},
    13: {"required": "call:ModuleList"},
    14: {"required": "ClassDef"},
    15: {"required": "call:apply"},
    16: {"required": "call:children"},
    17: {"required": "ClassDef"},
    18: {"required": "call:OrderedDict"},
}

WRONG = {
    1: ["layer = nn.Linear(d, out)\nresult = tuple(layer.weight.shape)"],
    2: ["result = (d, out)"],
    3: ["class Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.fc = nn.Linear(d, out, bias=False)\n\n\n"
        "result = sum(p.numel() for p in Model().parameters())"],
    4: ["class Twice(nn.Module):\n    def forward(self, x):\n        return x + 2\n\n\nresult = Twice()(x)"],
    5: ["result = [name for name, _ in model.named_modules()]", "result = list(model.state_dict().keys())[::-1]"],
    6: ["layer = nn.Linear(d, out, bias=bias)\nresult = sum(p.numel() for p in layer.parameters())"],
    7: ["class Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.weight = nn.Parameter(torch.tensor(values, dtype=torch.float32))\n"
         "        self.offset = nn.Parameter(torch.tensor(offsets, dtype=torch.float32))\n\n\nresult = sum(p.numel() for p in Model().parameters())"],
    8: ["layer = nn.Linear(2, 1, bias=False)\nwith torch.no_grad():\n    layer.weight.copy_(weight)\nresult = layer(x).squeeze(-1)"],
    9: ["model = nn.Sequential(nn.Linear(3, 4), nn.ReLU(), nn.Linear(4, 2))\nresult = tuple(x.shape)"],
    10: ["class Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.fc = nn.Linear(2, 2)\n\n    def forward(self, x):\n"
          "        return self.fc(x)\n\n\nmodel = Model()\nwith torch.no_grad():\n    model.fc.weight.copy_(weight)\n    model.fc.bias.copy_(bias)\nresult = model(x)"],
    11: ["result = sum(p.numel() for p in model.parameters())"],
    12: ["class Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.fc = nn.Linear(d, out)\n        self.running = torch.zeros(out)\n\n\n"
          "model = Model()\nresult = {k: tuple(v.shape) for k, v in model.state_dict().items()}"],
    13: ["class Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.layers = [nn.Linear(d, d) for _ in range(n)]\n\n\n"
          "result = sum(p.numel() for p in Model().parameters()) + 0 * len(nn.ModuleList())"],
    14: ["class Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        self.fc = nn.Linear(2, 2)\n\n    def forward(self, x):\n"
          "        return self.fc(x)\n\n\nmodel = Model()\nwith torch.no_grad():\n    model.fc.weight.copy_(weight)\n    model.fc.bias.copy_(bias)\nresult = model(x)"],
    15: ["def init(m):\n    if isinstance(m, nn.Linear):\n        nn.init.constant_(m.weight, value)\n\n\nmodel.apply(init)\nresult = model(x)"],
    16: ["result = [type(m).__name__ for m in model.modules()] + [type(m).__name__ for m in model.children()][:0]"],
    17: ["class Scale(nn.Module):\n    def __init__(self, factor):\n        super().__init__()\n        self.factor = factor\n\n    def forward(self, x):\n"
          "        return x + self.factor\n\n\nresult = Scale(factor)(x)"],
    18: ["model = nn.Sequential(OrderedDict([\n    (\"hidden\", nn.Linear(d, h)),\n    (\"act\", nn.ReLU()),\n    (\"out\", nn.Linear(h, 1)),\n]))\n"
          "result = tuple(model.out.weight.shape)"],
}


def compile_nn_modules(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
