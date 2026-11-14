"""PT07: optimizer steps. Oracles apply each update rule by hand in NumPy."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT07"
LESSONS = load_lessons(__file__)


def linear(weight, bias, x, y, extra=""):
    return (f"model = nn.Linear({len(weight[0])}, 1)\nwith torch.no_grad():\n"
            f"    model.weight.copy_(torch.tensor({weight!r}))\n    model.bias.fill_({bias!r})\n"
            f"x = torch.tensor({x!r})\ny = torch.tensor({y!r})" + extra)


ALTERNATIVES = {
    1: ["initial = [1.0]\nlr = 0.5", "initial = [0.0, 3.0, -4.0]\nlr = 0.05"],
    2: ["initial = [5.0]", "initial = [0.5, 1.5, -2.5]"],
    3: ["initial = [0.5]", "initial = [[1.0, 0.0], [-3.0, 2.0]]"],
    4: [linear([[0.0, 0.0]], 0.0, [[1.0, 1.0]], [[2.0]], "\nlr = 0.25"),
        linear([[2.0, 1.0, 0.0]], 1.0, [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [1.0, 1.0, 1.0]], [[0.0], [1.0], [2.0]], "\nlr = 0.1")],
    5: ["initial = [1.0]\ntarget = torch.tensor([-1.0])", "initial = [3.0, 3.0, 3.0]\ntarget = torch.tensor([1.0, 3.0, 7.0])"],
    6: ["initial = [1.0]\nnew_lr = 0.5", "initial = [4.0, -2.0, 0.0]\nnew_lr = 0.1"],
    7: ["initial = [1.0]\nlr = 0.25", "initial = [3.0, -3.0, 1.0]\nlr = 0.05"],
    8: ["initial = [1.0]\nlr = 0.1", "initial = [3.0, 4.0]\nlr = 0.5"],
    9: ["initial = [1.0]", "initial = [0.0, 3.0, -0.5]"],
    10: ["initial = [1.0]\nlr = 0.5", "initial = [-3.0, 4.0]\nlr = 0.01"],
    11: ["initial = [1.0]\ntarget = torch.tensor([5.0])\nweight_decay = 0.0",
         "initial = [4.0, 0.0, -2.0]\ntarget = torch.tensor([1.0, 1.0, 1.0])\nweight_decay = 0.1"],
    12: ["a_initial = [2.0]\nb_initial = [2.0]\nlr_a = 0.5\nlr_b = 0.0",
         "a_initial = [1.0, 0.0, -1.0]\nb_initial = [4.0, 1.0]\nlr_a = 0.25\nlr_b = 0.1"],
    13: ["x = torch.tensor([1.0, 2.0])\ny = torch.tensor([2.0, 4.0])\nlr = 0.05\nsteps = 2",
         "x = torch.tensor([-1.0, 0.0, 1.0, 2.0])\ny = torch.tensor([0.0, 1.0, 1.0, 3.0])\nlr = 0.2\nsteps = 4"],
    14: ["initial = 0.0\nx = torch.tensor([2.0, 2.0])", "initial = 0.5\nx = torch.tensor([1.0, -1.0, 2.0, 0.0, 3.0, 1.0])"],
    15: ["initial = [0.1, 0.2]\nmax_norm = 1.0", "initial = [1.0, 2.0, 2.0]\nmax_norm = 3.0"],
    16: ["model = nn.Linear(1, 1)\nwith torch.no_grad():\n    model.weight.fill_(0.0)\n    model.bias.fill_(2.0)\n"
          "x = torch.tensor([[1.0]])\ny = torch.tensor([[0.0]])",
          "model = nn.Linear(1, 1)\nwith torch.no_grad():\n    model.weight.fill_(-1.0)\n    model.bias.fill_(0.5)\n"
          "x = torch.tensor([[0.0], [1.0], [3.0]])\ny = torch.tensor([[1.0], [2.0], [0.0]])"],
    17: ["lr = 1.0", "lr = 0.08"],
    18: ["initial = [0.5]", "initial = [[2.0, 0.0], [-1.0, 1.0]]"],
}

_PRELUDE = """
import numpy as np
def _a(v):
    return np.asarray(v.tolist() if hasattr(v, "tolist") else v, dtype=np.float64)
def _f(a):
    return torch.from_numpy(np.array(a, dtype=np.float64, order="C")).to(torch.float32)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "_w = _a(initial)\nexpected = _f(_w - lr * 2 * _w)",
    2: "_w = _a(initial)\nexpected = (_f(_w), _f(_w - 0.1 * 2 * _w))",
    3: "_w = _a(initial)\nexpected = (_f(2 * _w), True)",
    4: ("_W, _b = _a(model.weight), _a(model.bias)\n_X, _Y = _a(x), _a(y)\n"
        "_r = _X @ _W.T + _b - _Y\nexpected = _f(_W - lr * 2 * _r.T @ _X / _r.size)"),
    5: "_w = _a(initial)\nexpected = _f(_w - 0.25 * 2 * (_w - _a(target)))",
    6: "_w = _a(initial)\nexpected = _f(_w - new_lr * 2 * _w)",
    7: "_w = _a(initial)\nfor _ in range(2):\n    _w = _w - lr * 2 * _w\nexpected = _f(_w)",
    8: ("_w, expected = _a(initial), []\nfor _ in range(3):\n    expected.append(float((_w ** 2).sum()))\n"
        "    _w = _w - lr * 2 * _w"),
    9: "_w = _a(initial)\n_v = np.zeros_like(_w)\nfor _ in range(2):\n    _v = 0.9 * _v + 2 * _w\n    _w = _w - 0.1 * _v\nexpected = _f(_w)",
    10: ("_w = _a(initial)\n_g = 2 * _w\n_m = 0.1 * _g / (1 - 0.9)\n_v = 0.001 * _g ** 2 / (1 - 0.999)\n"
         "expected = _f(_w - lr * _m / (np.sqrt(_v) + 1e-8))"),
    11: "_w = _a(initial)\nexpected = _f(_w - 0.1 * (1 + weight_decay * _w))",
    12: "expected = (_f(_a(a_initial) * (1 - 2 * lr_a)), _f(_a(b_initial) * (1 - 2 * lr_b)))",
    13: ("_X, _Y, _w, _b = _a(x), _a(y), 0.0, 0.0\nfor _ in range(steps):\n    _r = _w * _X + _b - _Y\n"
         "    _w, _b = _w - lr * 2 * np.mean(_r * _X), _b - lr * 2 * np.mean(_r)\nexpected = (_f(_w), _f(_b))"),
    14: "_X = _a(x)\n_g = 2 * np.mean(_X * (initial * _X - 1))\nexpected = _f(initial - 0.1 * _g)",
    15: ("_w = _a(initial)\n_g = 2 * _w\n_coef = max_norm / (np.sqrt((_g ** 2).sum()) + 1e-6)\n"
         "_g = _g * min(_coef, 1.0)\nexpected = _f(_w - _g)"),
    16: ("_W, _b = _a(model.weight), _a(model.bias)\n_X, _Y = _a(x), _a(y)\n_r = _X @ _W.T + _b - _Y\n"
         "expected = (_f(_W - 0.5 * 2 * _r.T @ _X / _r.size), _f(_b))"),
    17: "expected = [lr * 0.5 ** k for k in (1, 2, 3)]",
    18: "expected = _f(3 * _a(initial) ** 2)",
}.items()}

RULES = {
    1: {"required": "call:step"},
    2: {"required": "call:step"},
    3: {"required": "call:zero_grad"},
    4: {"required": "call:step"},
    5: {"required": "call:step"},
    6: {"required": "attr:param_groups"},
    7: {"required": "call:zero_grad"},
    8: {"required": "call:item"},
    9: {"required": "call:SGD"},
    10: {"required": "call:Adam"},
    11: {"required": "call:SGD"},
    12: {"required": "call:SGD"},
    13: {"required": "call:step"},
    14: {"required": "call-count:step:1"},
    15: {"required": "call:clip_grad_norm_"},
    16: {"required": "call:requires_grad_"},
    17: {"required": "call:StepLR"},
    18: {"required": "attr:state"},
}

WRONG = {
    1: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=lr)\noptimizer.zero_grad()\n"
        "(w ** 2).sum().backward()\nresult = w.detach()"],
    2: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.1)\noptimizer.zero_grad()\n"
        "(w ** 2).sum().backward()\noptimizer.step()\nresult = (w.detach().clone(), w.detach().clone())"],
    3: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.1)\n(w ** 2).sum().backward()\n"
        "grad = w.grad.clone()\noptimizer.zero_grad(set_to_none=False)\nresult = (grad, w.grad is None)"],
    4: ["optimizer = torch.optim.SGD(model.parameters(), lr=lr)\noptimizer.zero_grad()\nloss = nn.MSELoss()(model(x), y)\n"
        "loss.backward()\nresult = model.weight.detach().clone()"],
    5: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.5)\noptimizer.zero_grad()\n"
        "((w - target) ** 2).sum().backward()\noptimizer.step()\nresult = w.detach()"],
    6: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=1.0)\noptimizer.zero_grad()\n"
        "(w ** 2).sum().backward()\noptimizer.step()\noptimizer.param_groups[0][\"lr\"] = new_lr\nresult = w.detach()"],
    7: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=lr)\noptimizer.zero_grad()\n"
        "for _ in range(2):\n    (w ** 2).sum().backward()\n    optimizer.step()\nresult = w.detach()"],
    8: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=lr)\nresult = []\nfor _ in range(3):\n"
        "    optimizer.zero_grad()\n    loss = (w ** 2).sum()\n    loss.backward()\n    optimizer.step()\n    result.append((w ** 2).sum().item())"],
    9: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.1)\nfor _ in range(2):\n"
        "    optimizer.zero_grad()\n    (w ** 2).sum().backward()\n    optimizer.step()\nresult = w.detach()"],
    10: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=lr)\noptimizer.zero_grad()\n"
         "(w ** 2).sum().backward()\noptimizer.step()\nresult = w.detach()"],
    11: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.1)\noptimizer.zero_grad()\n"
         "(w - target).sum().backward()\noptimizer.step()\nresult = w.detach()"],
    12: ["a = nn.Parameter(torch.tensor(a_initial))\nb = nn.Parameter(torch.tensor(b_initial))\n"
         "optimizer = torch.optim.SGD([a, b], lr=lr_a)\noptimizer.zero_grad()\n((a ** 2).sum() + (b ** 2).sum()).backward()\n"
         "optimizer.step()\nresult = (a.detach(), b.detach())"],
    13: ["w = nn.Parameter(torch.tensor(0.0))\nb = nn.Parameter(torch.tensor(0.0))\noptimizer = torch.optim.SGD([w, b], lr=lr)\n"
         "for _ in range(steps):\n    loss = ((w * x + b - y) ** 2).mean()\n    loss.backward()\n    optimizer.step()\nresult = (w.detach(), b.detach())"],
    14: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.1)\nhalf = len(x) // 2\n"
         "for batch in (x[:half], x[half:]):\n    optimizer.zero_grad()\n    loss = ((w * batch - 1) ** 2).mean() / 2\n    loss.backward()\n"
         "optimizer.step()\nresult = w.detach()"],
    15: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=1.0)\noptimizer.zero_grad()\n"
         "(w ** 2).sum().backward()\noptimizer.step()\ntorch.nn.utils.clip_grad_norm_([w], max_norm)\nresult = w.detach()"],
    16: ["optimizer = torch.optim.SGD(model.parameters(), lr=0.5)\noptimizer.zero_grad()\nnn.MSELoss()(model(x), y).backward()\n"
         "optimizer.step()\nmodel.bias.requires_grad_(False)\nresult = (model.weight.detach().clone(), model.bias.detach().clone())"],
    17: ["w = nn.Parameter(torch.tensor([1.0]))\noptimizer = torch.optim.SGD([w], lr=lr)\n"
         "scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.5)\nresult = []\nfor _ in range(3):\n"
         "    result.append(scheduler.get_last_lr()[0])\n    optimizer.step()\n    scheduler.step()"],
    18: ["w = nn.Parameter(torch.tensor(initial))\noptimizer = torch.optim.SGD([w], lr=0.1, momentum=0.9)\noptimizer.zero_grad()\n"
         "(w ** 3).sum().backward()\noptimizer.step()\nresult = w.detach()"],
}


def compile_training(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
