"""PT03: reductions with dim/keepdim, broadcasting and matrix products.

Oracles compute in NumPy (float64) and cast back to the input dtype."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT03"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["x = torch.tensor([[1.0, 3.0]])", "x = torch.tensor([[0.5], [1.5], [-2.0]])"],
    2: ["x = torch.tensor([[1.5, -1.0]])", "x = torch.tensor([[1, 2], [3, 4], [5, 6]])"],
    3: ["x = torch.tensor([2.0])", "x = torch.tensor([[-1.0, 1.0, 3.0]])"],
    4: ["x = torch.tensor([[1, 9, 9]])", "x = torch.tensor([[0.5], [-0.5]])"],
    5: ["x = torch.tensor([[0.0, 0.0, 0.0]])", "x = torch.tensor([[1.0, 5.0], [6.0, 2.0], [-3.0, -3.0]])"],
    6: ["a = torch.tensor([1.0, 1.0])\nb = torch.tensor([2.0, -2.0])", "a = torch.tensor([3.0])\nb = torch.tensor([-1.5])"],
    7: ["x = torch.tensor([[5.0]])", "x = torch.tensor([[1.0, 3.0], [-2.0, 2.0], [4.0, 4.0]])"],
    8: ["x = torch.tensor([[1.0, 1.0]])\nw = torch.tensor([3.0])", "x = torch.ones(3, 1)\nw = torch.tensor([1.0, 2.0, 3.0])"],
    9: ["x = torch.ones(1, 3, 2, 2)", "x = torch.arange(24.0).reshape(3, 1, 2, 4)"],
    10: ["x = torch.tensor([[2.0, 0.0, 1.0]])\nw = torch.tensor([1.0, 5.0, -1.0])", "x = torch.eye(2)\nw = torch.tensor([3.0, 4.0])"],
    11: ["x = torch.tensor([[0.0], [2.0]])", "x = torch.tensor([[1.0, 2.0, 0.0], [2.0, 4.0, 1.0], [3.0, 9.0, 0.0], [4.0, 1.0, 1.0]])"],
    12: ["x = torch.tensor([[5.0, -5.0], [0.0, 2.0]])\nlow = -1.0\nhigh = 1.0", "x = torch.tensor([0.1, 0.9])\nlow = 0.2\nhigh = 0.5"],
    13: ["a = torch.tensor([[1.0, 2.0, 3.0]])\nb = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 1.0]])",
         "a = torch.eye(2)\nb = torch.tensor([[5.0, 6.0]])"],
    14: ["a = torch.ones(1, 2, 3)\nb = torch.arange(6.0).reshape(1, 3, 2)", "a = torch.eye(2).repeat(3, 1, 1)\nb = torch.arange(12.0).reshape(3, 2, 2)"],
    15: ["x = torch.tensor([[0.0, 0.0]])", "x = torch.tensor([[-1000.0, 1000.0], [2.0, 1.0], [0.0, -1.0]])"],
    16: ["x = torch.tensor([[1.0, 2.0, 2.0]])", "x = torch.tensor([[-5.0], [12.0]])"],
    17: ["x = torch.tensor([[3.0, 5.0]])\nmask = torch.tensor([[0.0, 1.0]])",
         "x = torch.tensor([[1.0, 1.0], [2.0, 4.0], [-1.0, 3.0]])\nmask = torch.tensor([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])"],
    18: ["a = torch.tensor([[1.0, 2.0, 3.0]])\nb = torch.tensor([[1.0, 2.0, 3.0], [0.0, 0.0, 0.0]])",
         "a = torch.tensor([[0.0], [2.0], [5.0]])\nb = torch.tensor([[1.0]])"],
}

_PRELUDE = """
import numpy as np
def _np(t):
    return np.asarray(t.tolist(), dtype=np.float64).reshape(tuple(t.shape))
def _t(a, dtype):
    return torch.from_numpy(np.array(a, dtype=np.float64, order="C")).to(dtype)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _t(_np(x).mean(axis=1), x.dtype)",
    2: "expected = _t(_np(x).sum(axis=0), x.dtype)",
    3: "expected = _t(_np(x).mean(), x.dtype)",
    4: "expected = _t(_np(x).max(axis=1), x.dtype)",
    5: "expected = torch.tensor([row.index(max(row)) for row in x.tolist()], dtype=torch.int64)",
    6: "expected = _t(float(np.dot(_np(a), _np(b))), a.dtype)",
    7: "_a = _np(x)\nexpected = _t(_a - _a.mean(axis=1, keepdims=True), x.dtype)",
    8: "expected = _t(_np(x) * _np(w)[:, None], x.dtype)",
    9: "expected = _t(_np(x).sum(axis=(0, 2, 3)), x.dtype)",
    10: "expected = _t(_np(x) @ _np(w), x.dtype)",
    11: "_a = _np(x)\nexpected = _t((_a - _a.mean(axis=0)) / _a.std(axis=0), x.dtype)",
    12: "expected = _t(np.minimum(np.maximum(_np(x), low), high), x.dtype)",
    13: "expected = _t(np.einsum('nd,md->nm', _np(a), _np(b)), a.dtype)",
    14: "expected = _t(np.einsum('bnd,bdm->bnm', _np(a), _np(b)), a.dtype)",
    15: "_a = _np(x)\n_e = np.exp(_a - _a.max(axis=1, keepdims=True))\nexpected = _t(_e / _e.sum(axis=1, keepdims=True), x.dtype)",
    16: "expected = _t(np.sqrt((_np(x) ** 2).sum(axis=1)), x.dtype)",
    17: "expected = _t((_np(x) * _np(mask)).sum(axis=1) / _np(mask).sum(axis=1), x.dtype)",
    18: "expected = _t(((_np(a)[:, None, :] - _np(b)[None, :, :]) ** 2).sum(axis=2), a.dtype)",
}.items()}

RULES = {
    12: {"required": "call:clamp"},
    15: {"required": "call:softmax"},
}

WRONG = {
    1: ["result = x.mean(dim=0)", "result = x.mean(dim=1, keepdim=True)"],
    2: ["result = x.sum(dim=1)"],
    3: ["result = x.mean(dim=0)", "result = x.sum()"],
    4: ["result = x.max(dim=0).values", "result = x.argmax(dim=1)"],
    5: ["result = x.argmax(dim=0)", "result = x.max(dim=1).values"],
    6: ["result = a * b", "result = (a + b).sum()"],
    7: ["result = x - x.mean(dim=0, keepdim=True)", "result = x - x.mean()"],
    8: ["result = x * w.unsqueeze(0)", "result = x * w.sum()"],
    9: ["result = x.sum(dim=(0, 1, 2))", "result = x.sum(dim=1)"],
    10: ["result = x * w", "result = w @ x.T @ x"],
    11: ["result = (x - x.mean(dim=0, keepdim=True)) / x.std(dim=0, keepdim=True)",
         "result = (x - x.mean(dim=1, keepdim=True)) / x.std(dim=1, correction=0, keepdim=True)"],
    12: ["result = torch.clamp(x, min=high, max=low)", "result = torch.clamp(x, min=low)"],
    13: ["result = a @ b", "result = (a * b).sum(dim=1)"],
    14: ["result = a * b", "result = (a @ b).sum(dim=0)"],
    15: ["result = torch.softmax(x, dim=0)", "result = torch.exp(x) / torch.exp(x).sum(dim=1, keepdim=True)"],
    16: ["result = (x ** 2).sum(dim=1)", "result = torch.linalg.vector_norm(x, dim=0)"],
    17: ["result = (x * mask).mean(dim=1)", "result = (x * mask).sum(dim=1) / mask.sum()"],
    18: ["diff = a[:, None, :] - b[None, :, :]\nresult = diff.abs().sum(dim=-1)", "result = (a @ b.T) ** 2"],
}


def compile_tensor_ops(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
