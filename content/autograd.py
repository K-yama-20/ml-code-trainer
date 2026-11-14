"""PT04: autograd. Oracles write each derivative out by hand."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT04"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["values = [-1.5]", "values = [[1.0, 0.0], [2.0, -3.0]]"],
    2: ["value = -1.0\na = 0.5", "value = 4.0\na = -2.0"],
    3: ["values = [5.0]", "values = [[1.0, 2.0], [3.0, 4.0]]"],
    4: ["value = 0.0", "value = -1.0"],
    5: ["values = [0.5]", "values = [[2.0, 0.0], [-1.0, 4.0]]"],
    6: ["a_values = [0.5]\nb_values = [4.0]", "a_values = [1.0, 0.0, -1.0]\nb_values = [2.0, 2.0, 2.0]"],
    7: ["value = -1.0\nc = 0.5", "value = 3.0\nc = -2.0"],
    8: ["values = [-1.0]", "values = [[0.5, 1.5]]"],
    9: ["values = [0.0, 3.0]", "values = [[1.0], [-2.0]]"],
    10: ["values = [4.0]\nupstream = torch.tensor([3.0])", "values = [1.0, 1.0]\nupstream = torch.tensor([0.0, -2.0])"],
    11: ["initial = [3.0]\nlr = 0.5", "initial = [1.0, 0.0, -1.0]\nlr = 0.25"],
    12: ["values = [1.0]", "values = [0.25, -0.5]"],
    13: ["pred_values = [0.0]\ntarget = torch.tensor([2.0])", "pred_values = [1.0, 1.0, 1.0, 1.0]\ntarget = torch.tensor([1.0, 2.0, 3.0, 4.0])"],
    14: ["x = torch.tensor([[2.0], [1.0]])\ny = torch.tensor([4.0, 1.0])\nw_values = [1.0]",
         "x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])\ny = torch.tensor([0.0, 0.0])\nw_values = [1.0, -1.0]"],
    15: ["value = -1.0", "value = 0.5"],
    16: ["values = [3.0]", "values = [[0.5, -0.5], [1.0, 0.0]]"],
    17: ["values = [-1.0, -3.0]", "values = [[0.0, 2.0], [7.0, 1.0]]"],
    18: ["values = [1.0, -2.0]", "values = [[0.0, 0.5], [-0.5, 0.0]]"],
}

_PRELUDE = """
import math
import numpy as np
def _f(a):
    return torch.tensor(np.asarray(a, dtype=np.float64).tolist(), dtype=torch.float32)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _f(2 * np.asarray(values))",
    2: "expected = _f(a)",
    3: "_a = np.asarray(values)\nexpected = _f(np.full(_a.shape, 1 / _a.size))",
    4: "expected = _f(3 * value ** 2 - 2)",
    5: "expected = _f(values)",
    6: "expected = (_f(b_values), _f(a_values))",
    7: "expected = _f(c)",
    8: "expected = _f(4 * np.asarray(values))",
    9: "expected = _f(3 * np.asarray(values) ** 2)",
    10: "expected = _f(2 * np.asarray(upstream.tolist()))",
    11: "_w = np.asarray(initial)\nexpected = _f(_w - lr * 2 * _w)",
    12: "expected = _f(2 * np.exp(2 * np.asarray(values)))",
    13: ("_p, _t = np.asarray(pred_values), np.asarray(target.tolist())\n"
         "expected = _f(2 * (_p - _t) / _p.size)"),
    14: ("_x, _y, _w = np.asarray(x.tolist()), np.asarray(y.tolist()), np.asarray(w_values)\n"
         "expected = _f(2 * _x.T @ (_x @ _w - _y) / len(_y))"),
    15: "expected = _f(6 * value)",
    16: "expected = _f(4 * np.asarray(values))",
    17: "_a = np.asarray(values)\n_g = np.zeros(_a.shape)\n_g[np.unravel_index(_a.argmax(), _a.shape)] = 1\nexpected = _f(_g)",
    18: "expected = _f((np.asarray(values) > 0).astype(float))",
}.items()}

_BACKWARD = {"required": "call:backward"}
RULES = {n: _BACKWARD for n in range(1, 19) if n != 15}
RULES[11] = {"required": 'all:["call:backward", "call:no_grad"]'}
RULES[15] = {"required": "call-count:grad:2"}
RULES[16] = {"required": 'all:["call-count:backward:2", "call-keywords:{\\"name\\": \\"backward\\", \\"keywords\\": {\\"retain_graph\\": true}}"]'}

WRONG = {
    1: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\n(x ** 2).sum().backward()\nresult = x"],
    2: ["x = torch.tensor(value, dtype=torch.float32, requires_grad=True)\n(a * x).backward()\nresult = x.grad * x.detach()"],
    3: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\nx.sum().backward()\nresult = x.grad"],
    4: ["x = torch.tensor(value, dtype=torch.float32, requires_grad=True)\ny = x ** 3 - 2 * x\ny.backward()\nresult = y.detach()"],
    5: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\n(x * x).sum().backward()\nresult = x.grad"],
    6: ["a = torch.tensor(a_values, dtype=torch.float32, requires_grad=True)\nb = torch.tensor(b_values, dtype=torch.float32, requires_grad=True)\n"
         "(a * b).sum().backward()\nresult = (b.grad, a.grad)"],
    7: ["x = torch.tensor(value, dtype=torch.float32, requires_grad=True)\n(x ** 2).backward()\n(c * x).backward()\nresult = x.grad"],
    8: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\n(x ** 2).sum().backward()\nresult = x.grad"],
    9: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\n(x ** 3).mean().backward()\nresult = x.grad"],
    10: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\ny = 2 * x\ny.sum().backward()\nresult = x.grad"],
    11: ["w = torch.tensor(initial, dtype=torch.float32, requires_grad=True)\n(w ** 2).sum().backward()\nwith torch.no_grad():\n"
          "    w += lr * w.grad\nresult = w"],
    12: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\ntorch.exp(x).sum().backward()\nresult = x.grad"],
    13: ["pred = torch.tensor(pred_values, dtype=torch.float32, requires_grad=True)\n((pred - target) ** 2).sum().backward()\nresult = pred.grad"],
    14: ["w = torch.tensor(w_values, dtype=torch.float32, requires_grad=True)\nloss = ((x @ w - y) ** 2).sum()\nloss.backward()\nresult = w.grad"],
    15: ["x = torch.tensor(value, dtype=torch.float32, requires_grad=True)\ny = x ** 3\n(g,) = torch.autograd.grad(y, x, create_graph=True)\n"
          "(g2,) = torch.autograd.grad(g, x)\nresult = g"],
    16: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\ny = (x ** 2).sum()\ny.backward(retain_graph=True)\n"
          "x.grad = None\ny.backward()\nresult = x.grad"],
    17: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\nx.sum().backward()\nresult = x.grad"],
    18: ["x = torch.tensor(values, dtype=torch.float32, requires_grad=True)\ntorch.relu(x).sum().backward()\nresult = (x.detach() >= 0).float()"],
}


def compile_autograd(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
