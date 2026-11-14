"""NP09: normalization and numerical stability.

Oracles compute every expected value element by element with ``math`` so they
stay independent of the vectorised reference solutions.
"""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "NP09"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["x = np.array([-1.0, -1.0, 2.0])", "x = np.array([0.5, 4.0, -3.5, 2.0])"],
    2: ["x = np.array([1.0, 1.0, 1.0, 1.0])", "x = np.array([-2.0, 0.0, 1.0, 2.0])"],
    3: ["x = np.array([-2.0, 2.0, 0.0])", "x = np.array([5.0, 5.5, 5.25, 6.0, 5.0])"],
    4: ["x = np.array([1.0, 3.0])", "x = np.array([10.0, 20.0, 60.0])"],
    5: ["x = np.array([[0.0, -2.0], [4.0, -2.0]])\neps = 1e-6",
        "x = np.array([[1e-9, 10.0, 3.0], [-1e-9, 20.0, 3.0]])\neps = 1e-8"],
    6: ["x = np.array([[5.0, -1.0], [5.0, 3.0]])",
        "x = np.array([[1e-12, 0.0, 9.0], [0.0, 0.0, 9.0], [2e-12, 0.0, 9.0]])"],
    7: ["x = np.array([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 1e-8]])\neps = 1e-4",
        "x = np.array([[-6.0, 8.0], [1e-7, 0.0]])\neps = 1e-6"],
    8: ["x = np.array([[0.0, 0.0, 0.0], [-1.0, 2.0, -1.0]])",
        "x = np.array([[5.0, 0.0], [0.0, -2.0], [0.0, 0.0]])"],
    9: ["test = np.array([[1.0, 2.0, 3.0]])\nmean = np.array([0.0, 2.0, 1.0])\nstd = np.array([1.0, 4.0, 1e-5])\neps = 1e-3",
        "test = np.array([[0.0], [2.0], [5.0]])\nmean = np.array([1.0])\nstd = np.array([0.5])\neps = 1e-8"],
    10: ["test = np.array([[0.0, 1.0, 2.0]])\ntrain_min = np.array([0.0, 0.0, 0.0])\ntrain_max = np.array([1.0, 2.0, 4.0])",
         "test = np.array([[15.0], [-10.0], [0.0]])\ntrain_min = np.array([-5.0])\ntrain_max = np.array([5.0])"],
    11: ["x = np.array([1e-10, -0.5, 3.0])", "x = np.array([[1e-16, 2.0], [-1e-16, 0.0]])"],
    12: ["x = np.array([1e-10, -0.5, 2.0])", "x = np.array([[1e-16, 0.5], [-1e-16, 0.0]])"],
    13: ["x = np.array([[500.0, -500.0], [1.0, -1.0]])", "x = np.array([0.0, -800.0, 30.0])"],
    14: ["a = np.array([[-1000.0, 1000.0], [5.0, 0.0]])\nb = np.array([[0.0, 999.0], [5.0, -1000.0]])",
         "a = np.array([700.0, -3.0])\nb = np.array([-700.0, -3.0])"],
    15: ["x = np.array([[-1000.0, -999.0], [5.0, 5.0]])", "x = np.array([[0.0], [700.0], [-3.0]])"],
    16: ["x = np.array([[-1000.0, 1000.0], [0.0, 0.0]])", "x = np.array([[2.0, 0.0, -2.0, 0.0]])"],
    17: ["x = np.array([[-1000.0, -1000.0]])", "x = np.array([[0.0], [5.0], [-700.0]])"],
    18: ["x = np.array([[-500.0, 500.0]])", "x = np.array([[0.0, 0.0], [3.0, 1.0], [800.0, -800.0]])"],
}

_ELEMENTWISE = """
import math
def _map(f, a):
    return np.array([f(v) for v in a.ravel().tolist()], dtype=np.float64).reshape(a.shape)
def _rows(f, a):
    return np.array([f(row) for row in a.tolist()], dtype=np.float64)
def _lse(row):
    m = max(row)
    return m + math.log(sum(math.exp(v - m) for v in row))
"""


def _oracle(body):
    return _ELEMENTWISE + body


ORACLES = {n: _oracle(body) for n, body in {
    1: "s = sum(abs(v) for v in x.ravel().tolist())\nexpected = _map(lambda v: v / s, x)",
    2: "s = math.sqrt(sum(v * v for v in x.tolist()))\nexpected = _map(lambda v: v / s, x)",
    3: "lo, hi = min(x.tolist()), max(x.tolist())\nexpected = _map(lambda v: (v - lo) / (hi - lo), x)",
    4: ("mu = sum(x.tolist()) / len(x)\nsd = math.sqrt(sum((v - mu) ** 2 for v in x.tolist()) / len(x))\n"
        "expected = _map(lambda v: (v - mu) / sd, x)"),
    5: ("cols = x.T.tolist()\nmus = [sum(c) / len(c) for c in cols]\n"
        "sds = [max(math.sqrt(sum((v - m) ** 2 for v in c) / len(c)), eps) for c, m in zip(cols, mus)]\n"
        "expected = np.array([[(v - mus[j]) / sds[j] for j, v in enumerate(row)] for row in x.tolist()])"),
    6: ("cols = x.T.tolist()\nlos = [min(c) for c in cols]\nspans = [max(c) - min(c) for c in cols]\n"
        "expected = np.array([[0.0 if spans[j] == 0 else (v - los[j]) / spans[j] for j, v in enumerate(row)]"
        " for row in x.tolist()])"),
    7: ("expected = np.array([[v / max(math.sqrt(sum(u * u for u in row)), eps) for v in row]"
        " for row in x.tolist()])"),
    8: ("expected = np.array([[0.0 if sum(abs(u) for u in row) == 0 else v / sum(abs(u) for u in row)"
        " for v in row] for row in x.tolist()])"),
    9: ("expected = np.array([[(v - mean[j]) / max(std[j], eps) for j, v in enumerate(row)]"
        " for row in test.tolist()])"),
    10: ("expected = np.array([[(v - train_min[j]) / (train_max[j] - train_min[j]) for j, v in enumerate(row)]"
         " for row in test.tolist()])"),
    11: "expected = _map(math.log1p, x)",
    12: "expected = _map(math.expm1, x)",
    13: ("def _sig(v):\n    if v >= 0:\n        return 1 / (1 + math.exp(-v))\n    e = math.exp(v)\n    return e / (1 + e)\n"
         "expected = _map(_sig, x)"),
    14: ("expected = np.array([max(p, q) + math.log1p(math.exp(-abs(p - q)))"
         " for p, q in zip(a.ravel().tolist(), b.ravel().tolist())]).reshape(a.shape)"),
    15: "expected = np.array([[math.exp(v - max(row)) for v in row] for row in x.tolist()])",
    16: ("expected = np.array([[math.exp(v - max(row)) / sum(math.exp(u - max(row)) for u in row)"
         " for v in row] for row in x.tolist()])"),
    17: "expected = _rows(_lse, x)",
    18: "expected = np.array([[v - _lse(row) for v in row] for row in x.tolist()])",
}.items()}

RULES = {
    2: {"required": "call:norm"},
    8: {"strict_division": True},
    11: {"required": "call:log1p", "comparison": "relative"},
    12: {"required": "call:expm1", "comparison": "relative"},
    13: {"strict_overflow": True},
    14: {"required": "call:logaddexp", "strict_overflow": True},
    15: {"strict_overflow": True},
    16: {"strict_overflow": True},
    17: {"strict_overflow": True},
    18: {"strict_overflow": True},
}

# Representative mistakes. Validation requires every one to be rejected.
WRONG = {
    1: ["result = x / x.sum()"],
    2: ["result = x / np.linalg.norm(x, 1)"],
    3: ["result = x / x.max()"],
    4: ["result = (x - x.mean()) / x.std(ddof=1)"],
    5: ["result = (x - x.mean(axis=0)) / np.where(x.std(axis=0) == 0, 1, x.std(axis=0))",
        "result = (x - x.mean(axis=0)) / np.maximum(x.std(axis=0, ddof=1), eps)"],
    6: ["result = (x - x.min(axis=0)) / np.maximum(np.ptp(x, axis=0), 1e-8)"],
    7: ["result = x / np.maximum(np.linalg.norm(x, axis=0, keepdims=True), eps)",
        "result = np.nan_to_num(x / np.linalg.norm(x, axis=1, keepdims=True))"],
    8: ["s = np.abs(x).sum(axis=1, keepdims=True)\nresult = np.where(s == 0, 0.0, x / s)",
        "result = x / np.maximum(np.abs(x).sum(axis=0, keepdims=True), 1e-12)"],
    9: ["result = (test - test.mean(axis=0)) / np.maximum(test.std(axis=0), eps)",
        "result = (test - mean) / (std + eps)"],
    10: ["result = np.clip((test - train_min) / (train_max - train_min), 0, 1)",
         "result = (test - test.min(axis=0)) / (test.max(axis=0) - test.min(axis=0))"],
    11: ["result = np.log(1 + x)"],
    12: ["result = np.exp(x) - 1"],
    13: ["result = 1 / (1 + np.exp(-x))",
         "z = np.exp(-np.abs(x))\nresult = np.where(x >= 0, z / (1 + z), 1 / (1 + z))"],
    14: ["result = np.log(np.exp(a) + np.exp(b))", "result = np.maximum(a, b)"],
    15: ["result = np.exp(x - x.max())", "result = np.exp(x) / np.exp(x.max(axis=1, keepdims=True))"],
    16: ["e = np.exp(x - x.max(axis=1, keepdims=True))\nresult = e / e.sum(axis=0, keepdims=True)",
         "e = np.exp(x)\nresult = e / e.sum(axis=1, keepdims=True)"],
    17: ["m = x.max(axis=1, keepdims=True)\nresult = m + np.log(np.exp(x - m).sum(axis=1, keepdims=True))",
         "result = np.log(np.exp(x).sum(axis=1))"],
    18: ["e = np.exp(x - x.max(axis=1, keepdims=True))\nresult = np.log(e / e.sum(axis=1, keepdims=True))"],
}


def compile_normalization(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
