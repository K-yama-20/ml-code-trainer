"""PT02: reshaping, permuting, concatenating and splitting tensors.

Oracles redo each layout change in NumPy and convert back with the input
dtype, so they never call the torch operation under test."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT02"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["x = torch.arange(12.0).reshape(3, 2, 2)", "x = torch.ones(1, 5)"],
    2: ["x = torch.tensor([7, 8])", "x = torch.zeros(2, 1, 3)"],
    3: ["x = torch.tensor([[1, 2], [3, 4]])", "x = torch.tensor([5.5])"],
    4: ["x = torch.arange(6.0).reshape(2, 3, 1)", "x = torch.ones(1, 1)"],
    5: ["x = torch.arange(12.0)\nrows = 4\ncols = 3", "x = torch.tensor([[1, 2], [3, 4]])\nrows = 1\ncols = 4"],
    6: ["x = torch.tensor([[1.5], [2.5]])", "x = torch.arange(9).reshape(3, 3)"],
    7: ["x = torch.arange(12).reshape(3, 4).T", "x = torch.arange(8.0).reshape(2, 2, 2).permute(2, 1, 0)"],
    8: ["x = torch.arange(48).reshape(2, 2, 4, 3)", "x = torch.arange(6.0).reshape(1, 1, 2, 3)"],
    9: ["x = torch.arange(12).reshape(3, 4)", "x = torch.tensor([[1.5, -1.0]])"],
    10: ["a = torch.tensor([[1.0, 2.0, 3.0]])\nb = torch.tensor([[4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])",
         "a = torch.zeros(0, 2)\nb = torch.ones(1, 2)"],
    11: ["a = torch.tensor([[1, 2], [3, 4]])\nb = torch.tensor([[5, 6], [7, 8]])", "a = torch.tensor([0.5])\nb = torch.tensor([1.5])"],
    12: ["x = torch.arange(12.0).reshape(1, 3, 2, 2)", "x = torch.arange(16).reshape(2, 1, 4, 2)"],
    13: ["a = torch.tensor([[1, 2, 3]])\nb = torch.tensor([[4, 5]])", "a = torch.ones(3, 1)\nb = torch.zeros(3, 2)"],
    14: ["x = torch.arange(6.0).reshape(3, 2)\nsizes = [1, 1, 1]", "x = torch.arange(8).reshape(4, 2)\nsizes = [3, 1]"],
    15: ["x = torch.tensor([[1.5, -1.0, 0.0]])\ntimes = 3", "x = torch.arange(6).reshape(3, 2)\ntimes = 1"],
    16: ["x = torch.arange(24.0).reshape(2, 4, 3)", "x = torch.arange(6).reshape(3, 2, 1)"],
    17: ["x = torch.arange(24).reshape(2, 2, 2, 3)", "x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])"],
    18: ["tensors = [torch.tensor([1.0, 2.0]), torch.tensor([3.0, 4.0]), torch.tensor([5.0, 6.0])]",
         "tensors = [torch.zeros(2, 1, dtype=torch.int64)]"],
}

_PRELUDE = """
import numpy as np
def _np(t):
    return np.asarray(t.tolist(), dtype=np.float64).reshape(tuple(t.shape))
def _t(a, like):
    return torch.from_numpy(np.array(a, order="C")).to(like.dtype)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _t(_np(x).reshape(x.shape[0], int(np.prod(x.shape[1:]))), x)",
    2: "expected = _t(_np(x)[np.newaxis], x)",
    3: "expected = _t(_np(x)[..., np.newaxis], x)",
    4: "expected = _t(_np(x)[..., 0], x)",
    5: "expected = _t(_np(x).reshape(rows, cols), x)",
    6: "expected = _t(_np(x).swapaxes(0, 1), x)",
    7: "expected = _t(_np(x).ravel(), x)",
    8: "expected = _t(np.moveaxis(_np(x), 3, 1), x)",
    9: "expected = _t(_np(x).T.ravel(), x)",
    10: "expected = _t(np.vstack([_np(a), _np(b)]), a)",
    11: "expected = _t(np.array([_np(a), _np(b)]), a)",
    12: "_a = _np(x)\nexpected = _t(_a.reshape(_a.shape[0], _a.shape[1] * _a.shape[2], _a.shape[3]), x)",
    13: "expected = _t(np.hstack([_np(a), _np(b)]), a)",
    14: "_a, _out, _s = _np(x), [], 0\nfor _k in sizes:\n    _out.append(_t(_a[_s:_s + _k], x))\n    _s += _k\nexpected = tuple(_out)",
    15: "expected = _t(np.tile(_np(x), (times, 1)), x)",
    16: "expected = _t(np.transpose(_np(x), (2, 0, 1)), x)",
    17: "_a = _np(x)\nexpected = _t(_a.reshape(-1, _a.shape[-1]), x)",
    18: "expected = _t(np.stack([_np(t) for t in tensors], axis=-1), tensors[0])",
}.items()}

RULES = {
    8: {"required": "call:permute"},
    14: {"required": "call:split"},
    16: {"required": "call:permute"},
}

WRONG = {
    1: ["result = x.reshape(-1)", "result = x.reshape(-1, x.shape[-1])"],
    2: ["result = x.unsqueeze(-1)"],
    3: ["result = x.unsqueeze(0)"],
    4: ["result = x.squeeze()"],
    5: ["result = x.reshape(cols, rows)", "result = x.reshape(cols, rows).T"],
    6: ["result = x.reshape(x.shape[1], x.shape[0])"],
    7: ["result = x.contiguous().T.reshape(-1)", "result = x.T.reshape(-1)"],
    8: ["result = x.reshape(x.shape[0], x.shape[3], x.shape[1], x.shape[2])", "result = x.permute(0, 3, 2, 1)"],
    9: ["result = x.reshape(-1)"],
    10: ["result = torch.cat([b, a], dim=0)", "result = torch.stack([a, b], dim=0)"],
    11: ["result = torch.cat([a, b], dim=0)", "result = torch.stack([a, b], dim=-1)"],
    12: ["result = torch.flatten(x, start_dim=1)", "result = torch.flatten(x, start_dim=2)"],
    13: ["result = torch.cat([b, a], dim=1)", "result = torch.cat([a, b], dim=0)"],
    14: ["result = torch.split(x, sizes[0], dim=0)", "result = torch.split(x, sizes, dim=1)"],
    15: ["result = x.repeat(1, times)", "result = x.repeat_interleave(times, dim=0)"],
    16: ["result = x.reshape(x.shape[2], x.shape[0], x.shape[1])", "result = x.permute(2, 1, 0)"],
    17: ["result = x.reshape(x.shape[0], -1)", "result = x.reshape(x.shape[-1], -1)"],
    18: ["result = torch.stack(tensors, dim=0)", "result = torch.cat(tensors, dim=-1)"],
}


def compile_tensor_shapes(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
