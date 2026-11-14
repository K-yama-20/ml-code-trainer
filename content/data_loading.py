"""PT08: Dataset and DataLoader. Oracles slice the source tensors directly;
shuffles use the documented ``torch.randperm(n, generator=...)`` order."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT08"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["x = torch.ones(1, 3)\ny = torch.zeros(1)", "x = torch.zeros(0, 2)\ny = torch.zeros(0)"],
    2: ["x = torch.tensor([[7.0], [8.0]])\ny = torch.tensor([5, 6])\nindex = 0",
        "x = torch.arange(12.0).reshape(4, 3)\ny = torch.tensor([1, 1, 0, 2])\nindex = -1"],
    3: ["n = 0\nbatch = 4", "n = 8\nbatch = 3"],
    4: ["n = 1\nbatch = 8", "n = 9\nbatch = 4"],
    5: ["x = torch.ones(1, 2)\nbatch = 8", "x = torch.arange(6.0).reshape(3, 2)\nbatch = 1"],
    6: ["x = torch.zeros(4, 1)\nbatch = 4", "x = torch.zeros(7, 2)\nbatch = 3"],
    7: ["x = torch.ones(1, 2)\ny = torch.zeros(1)\nbatch = 8", "x = torch.arange(6.0).reshape(3, 2)\ny = torch.tensor([9, 8, 7])\nbatch = 1"],
    8: ["x = torch.ones(1, 2)\nbatch = 8", "x = torch.arange(6.0).reshape(3, 2)\nbatch = 1"],
    9: ["values = [0.5]\nbatch = 4", "values = [-1.0, 2.0, 3.0, 4.0]\nbatch = 3"],
    10: ["n = 5\nseed = 1", "n = 8\nseed = 42"],
    11: ["x = torch.zeros(3, 1)\ny = torch.tensor([2, 3, 4])\nbatch = 3", "x = torch.zeros(4, 1)\ny = torch.tensor([5, 0, 1, 2])\nbatch = 1"],
    12: ["n = 6\nk = 4\nseed = 1", "n = 10\nk = 3\nseed = 7"],
    13: ["x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])\nindices = [1]", "x = torch.arange(6.0).reshape(6, 1)\nindices = [5, 4, 3, 2]"],
    14: ["sequences = [torch.tensor([1]), torch.tensor([2, 3, 4, 5])]\nbatch = 2",
         "sequences = [torch.tensor([9, 8]), torch.tensor([7, 6]), torch.tensor([5])]\nbatch = 3"],
    15: ["x = torch.tensor([[2.0], [4.0]])\nbatch = 4", "x = torch.tensor([[1.0, -1.0], [3.0, 0.0], [5.0, 4.0]])\nbatch = 1"],
    16: ["n = 4\nbatch = 4", "n = 2\nbatch = 5"],
    17: ["x = torch.tensor([[0.5]])\ny = torch.tensor([3])\nbatch = 4",
          "x = torch.arange(8.0).reshape(4, 2)\ny = torch.tensor([1, 0, 1, 0])\nbatch = 3"],
    18: ["x = torch.tensor([1.0, 1.0])\ny = torch.tensor([3.0, 3.0])\nbatch = 1",
          "x = torch.tensor([1.0, -1.0, 2.0])\ny = torch.tensor([1.0, -1.0, 2.0])\nbatch = 2"],
}

_PRELUDE = "import math\n"

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = x.shape[0]",
    2: "expected = (x[index].clone(), y[index].clone())",
    3: "expected = math.ceil(n / batch)",
    4: "expected = n // batch",
    5: "expected = x[:batch].clone()",
    6: "expected = [(min(batch, len(x) - s), *x.shape[1:]) for s in range(0, len(x), batch)]",
    7: "expected = (x[:batch].clone(), y[:batch].clone())",
    8: "expected = x.clone()",
    9: "expected = (torch.tensor(values[:batch]), torch.tensor([v * v for v in values[:batch]]))",
    # The DataLoader draws a base seed from the generator before sampling, so
    # the reference order comes from an equivalent loader over plain indices.
    10: ("from torch.utils.data import DataLoader as _DL\n"
         "expected = next(iter(_DL(list(range(n)), batch_size=n, shuffle=True,"
         " generator=torch.Generator().manual_seed(seed))))"),
    11: "_y = y.tolist()\nexpected = [sum(_y[s:s + batch]) for s in range(0, len(_y), batch)]",
    12: "expected = torch.randperm(n, generator=torch.Generator().manual_seed(seed)).tolist()[:k]",
    13: "expected = torch.tensor([x.tolist()[i] for i in indices])",
    14: ("_seqs = [s.tolist() for s in sequences[:batch]]\n_m = max(len(s) for s in _seqs)\n"
         "expected = torch.tensor([s + [0] * (_m - len(s)) for s in _seqs])"),
    15: "_rows = x.tolist()\nexpected = torch.tensor([sum(c) / len(_rows) for c in zip(*_rows)])",
    16: "expected = (n // batch) * batch",
    17: "expected = {'x': x[:batch].clone(), 'y': y[:batch].clone()}",
    18: ("_x, _y, _w = x.tolist(), y.tolist(), 0.0\nfor s in range(0, len(_x), batch):\n"
          "    _xb, _yb = _x[s:s + batch], _y[s:s + batch]\n"
          "    _g = sum(2 * (_w * a - b) * a for a, b in zip(_xb, _yb)) / len(_xb)\n    _w -= 0.1 * _g\n"
          "expected = torch.tensor(_w, dtype=torch.float32)"),
}.items()}

RULES = {
    1: {"required": "call:TensorDataset"},
    2: {"required": "call:TensorDataset"},
    3: {"required": "call:DataLoader"},
    4: {"required": "call:DataLoader"},
    5: {"required": "call:DataLoader"},
    6: {"required": "call:DataLoader"},
    7: {"required": "call:TensorDataset"},
    8: {"required": "call:DataLoader"},
    9: {"required": "ClassDef"},
    10: {"required": "call:DataLoader"},
    11: {"required": "call:DataLoader"},
    12: {"required": "call:random_split"},
    13: {"required": "call:Subset"},
    14: {"required": "call:pad_sequence"},
    15: {"required": "call:DataLoader"},
    16: {"required": "call:DataLoader"},
    17: {"required": "ClassDef"},
    18: {"required": "call:DataLoader"},
}

WRONG = {
    1: ["result = x.numel() + 0 * len(TensorDataset(x, y))"],
    2: ["dataset = TensorDataset(x, y)\nresult = (dataset[index][1], dataset[index][0])"],
    3: ["dataset = TensorDataset(torch.arange(n))\nresult = len(DataLoader(dataset, batch_size=batch, drop_last=True))"],
    4: ["dataset = TensorDataset(torch.arange(n))\nresult = len(DataLoader(dataset, batch_size=batch, drop_last=False))"],
    5: ["loader = DataLoader(TensorDataset(x), batch_size=batch, shuffle=False)\nresult = list(loader)[-1][0]"],
    6: ["loader = DataLoader(TensorDataset(x), batch_size=batch, shuffle=False, drop_last=True)\nresult = [tuple(xb.shape) for (xb,) in loader]"],
    7: ["loader_x = DataLoader(TensorDataset(x), batch_size=batch, shuffle=False)\nloader_y = DataLoader(TensorDataset(y.flip(0)), batch_size=batch, shuffle=False)\n"
        "result = (next(iter(loader_x))[0], next(iter(loader_y))[0])"],
    8: ["loader = DataLoader(TensorDataset(x), batch_size=batch, shuffle=False, drop_last=True)\nresult = torch.cat([xb for (xb,) in loader], dim=0)"],
    9: ["class SquareDataset(Dataset):\n    def __init__(self, values):\n        self.values = values\n\n    def __len__(self):\n        return len(self.values)\n\n"
        "    def __getitem__(self, i):\n        v = self.values[i]\n        return torch.tensor(v), torch.tensor(v * 2)\n\n\n"
        "xb, yb = next(iter(DataLoader(SquareDataset(values), batch_size=batch)))\nresult = (xb, yb)"],
    10: ["loader = DataLoader(TensorDataset(torch.arange(n)), batch_size=n, shuffle=False)\nresult = next(iter(loader))[0]"],
    11: ["loader = DataLoader(TensorDataset(x, y), batch_size=batch, shuffle=False)\nresult = [int(yb.sum()) for xb, yb in loader][::-1]",
         "loader = DataLoader(TensorDataset(x, y), batch_size=batch, shuffle=False)\nresult = [len(yb) for xb, yb in loader]"],
    12: ["first, second = random_split(TensorDataset(torch.arange(n)), [k, n - k], generator=torch.Generator().manual_seed(seed))\n"
          "result = list(second.indices)"],
    13: ["subset = Subset(TensorDataset(x), sorted(indices))\nloader = DataLoader(subset, batch_size=2, shuffle=False)\n"
          "result = torch.cat([xb for (xb,) in loader], dim=0)"],
    14: ["def pad_batch(batch):\n    return torch.nn.utils.rnn.pad_sequence(batch, batch_first=False)\n\n\n"
          "loader = DataLoader(sequences, batch_size=batch, collate_fn=pad_batch)\nresult = next(iter(loader))"],
    15: ["loader = DataLoader(TensorDataset(x), batch_size=batch)\nresult = torch.stack([xb.mean(dim=0) for (xb,) in loader]).mean(dim=0)"],
    16: ["loader = DataLoader(TensorDataset(torch.arange(n)), batch_size=batch, drop_last=False)\nresult = sum(len(xb) for (xb,) in loader)"],
    17: ["class DictDataset(Dataset):\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n\n    def __len__(self):\n        return len(self.x)\n\n"
          "    def __getitem__(self, i):\n        return {\"x\": self.x[i], \"y\": self.y[i]}\n\n\nresult = list(DataLoader(DictDataset(x, y), batch_size=batch))[-1]"],
    18: ["w = nn.Parameter(torch.tensor(0.0))\noptimizer = torch.optim.SGD([w], lr=0.1)\nloader = DataLoader(TensorDataset(x, y), batch_size=batch, shuffle=False)\n"
          "optimizer.zero_grad()\nfor xb, yb in loader:\n    ((w * xb - yb) ** 2).mean().backward()\n    optimizer.step()\nresult = w.detach()"],
}


def compile_data_loading(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
