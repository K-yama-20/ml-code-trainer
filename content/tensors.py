"""PT01: creating CPU tensors and controlling dtype, shape and copies."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT01"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["values = [[1, 2], [3, 4]]", "values = [-0.5, 2.5]"],
    2: ["labels = [3]", "labels = [1, 1, 0, 4]"],
    3: ["x = torch.zeros(4)", "x = torch.ones(1, 2, 5)"],
    4: ["x = torch.tensor([1.0, 2.0])", "x = torch.tensor([True, False])"],
    5: ["x = torch.tensor([1.5, -2.0])", "x = torch.ones(2, 1, 3, dtype=torch.float64)"],
    6: ["rows = 1\ncols = 4", "rows = 3\ncols = 1"],
    7: ["x = torch.tensor([[0.5], [1.5]])", "x = torch.tensor([True, False, True])"],
    8: ["x = torch.ones(5)", "x = torch.zeros(0, 3)"],
    9: ["start = 2\nend = 5\nstep = 1", "start = -1\nend = 0.5\nstep = 0.5"],
    10: ["a = np.array([1, 2, 3], dtype=np.int64)", "a = np.array([[0.5]], dtype=np.float32)"],
    11: ["x = torch.tensor([1, 2, 3])", "x = torch.tensor([[0.25]], dtype=torch.float64)"],
    12: ["x = torch.tensor([[1, 2], [3, 5]])", "x = torch.tensor([-3, 4])"],
    13: ["n = 1\nd = 5", "n = 4\nd = 1"],
    14: ["x = torch.tensor([1, 2, 3])\nvalue = 2", "x = torch.zeros(2, 1, dtype=torch.float64)\nvalue = -0.5"],
    15: ["x = torch.tensor([1, 2, 3])", "x = torch.tensor([[-0.25]])"],
    16: ["x = torch.tensor([1, 2, 3])\nthreshold = 2", "x = torch.tensor([[0.0], [-0.1]])\nthreshold = -0.5"],
    17: ["a = torch.tensor([[2], [4]])\nb = torch.tensor([[0.5], [1.5]])", "a = torch.tensor([-1])\nb = torch.tensor([10.0])"],
    18: ["x = torch.tensor([0.0, 0.0])\nindex = 0\nvalue = -1.0", "x = torch.tensor([5.0, 6.0, 7.0, 8.0])\nindex = 3\nvalue = 0.5"],
}

_PRELUDE = "import numpy as np\nimport math\n"

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = torch.from_numpy(np.asarray(values, dtype=np.float32))",
    2: "expected = torch.from_numpy(np.asarray(labels, dtype=np.int64))",
    3: "expected = tuple(int(v) for v in x.size())",
    4: "expected = {torch.int64: 'torch.int64', torch.float32: 'torch.float32', torch.bool: 'torch.bool'}[x.dtype]",
    5: "expected = torch.zeros(tuple(x.shape), dtype=x.dtype)",
    6: "expected = torch.from_numpy(np.ones((rows, cols), dtype=np.float64))",
    7: "expected = torch.from_numpy(np.asarray(x.tolist(), dtype=np.float64))",
    8: "expected = math.prod(x.shape)",
    9: ("_vals, _v = [], float(start)\nwhile _v < end - 1e-12:\n    _vals.append(_v)\n    _v += step\n"
        "expected = torch.tensor(_vals, dtype=torch.float32)"),
    10: "expected = torch.tensor(a.tolist(), dtype={'float64': torch.float64, 'int64': torch.int64, 'float32': torch.float32}[str(a.dtype)])",
    11: "expected = np.asarray(x.tolist(), dtype={torch.float32: np.float32, torch.int64: np.int64, torch.float64: np.float64}[x.dtype])",
    12: "_flat = x.flatten().tolist()\nexpected = torch.tensor(sum(_flat) / len(_flat), dtype=torch.float32)",
    13: "expected = (n, d)",
    14: "expected = torch.tensor(np.full(tuple(x.shape), value).tolist(), dtype=x.dtype)",
    15: "expected = float(sum(x.flatten().tolist()))",
    16: "expected = torch.tensor([[v > threshold for v in row] for row in x.reshape(len(x), -1).tolist()]).reshape(x.shape)",
    17: "expected = torch.tensor((np.asarray(a.tolist()) + np.asarray(b.tolist())).tolist(), dtype=torch.float32)",
    18: "_y = x.tolist()\n_y[index] = value\nexpected = (torch.tensor(x.tolist()), torch.tensor(_y))",
}.items()}

RULES = {
    10: {"required": "call:from_numpy"},
    13: {"required": "call:randn"},
    18: {"required": "call:clone", "protect_inputs": True},
}

WRONG = {
    1: ["result = torch.tensor(values)", "result = torch.tensor(values, dtype=torch.float64)"],
    2: ["result = torch.tensor(labels, dtype=torch.float32)", "result = torch.tensor(labels, dtype=torch.int32)"],
    3: ["result = (x.shape[-1], x.shape[0])", "result = (len(x),)"],
    4: ["result = str(x.type())"],
    5: ["result = torch.zeros(x.shape)"],
    6: ["result = torch.ones(rows, cols)", "result = torch.ones(cols, rows, dtype=torch.float64)"],
    7: ["result = x.to(device=\"cpu\", dtype=torch.float32)"],
    8: ["result = x.dim()", "result = len(x)"],
    9: ["result = torch.arange(start, end, step)", "result = torch.linspace(start, end, 4)"],
    10: ["result = torch.tensor(a, dtype=torch.float32) + 0 * torch.from_numpy(a)"],
    11: ["result = x.tolist()", "result = x.numpy().astype(np.float64)"],
    12: ["result = x.float().sum()", "result = x.double().mean()"],
    13: ["x = torch.randn(d, n)\nresult = tuple(x.shape)"],
    14: ["result = torch.full(tuple(x.shape), value)"],
    15: ["result = x.sum()", "result = x.mean().item()"],
    16: ["result = (x > threshold).int()", "result = x >= threshold"],
    17: ["result = (a + b).double()", "result = a + b.long()"],
    18: ["y = x\ny[index] = value\nresult = (x, y)"],
}


def compile_tensors(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
