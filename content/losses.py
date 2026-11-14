"""PT06: losses and logits. Oracles write each loss formula out in NumPy."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PT06"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["pred = torch.tensor([[0.0, 1.0], [2.0, 2.0]])\ntarget = torch.tensor([[1.0, 1.0], [0.0, 2.0]])",
        "pred = torch.tensor([-1.0])\ntarget = torch.tensor([1.0])"],
    2: ["pred = torch.tensor([1.0, -1.0])\ntarget = torch.tensor([1.0, 1.0])", "pred = torch.tensor([0.5])\ntarget = torch.tensor([2.0])"],
    3: ["pred = torch.tensor([[0.0, 1.0], [2.0, 2.0]])\ntarget = torch.tensor([[1.0, 1.0], [0.0, 2.0]])",
        "pred = torch.tensor([-1.0])\ntarget = torch.tensor([1.0])"],
    4: ["pred = torch.tensor([[0.0, 1.0], [2.0, 2.0]])\ntarget = torch.tensor([[1.0, 1.0], [0.0, 5.0]])",
        "pred = torch.tensor([-1.0])\ntarget = torch.tensor([1.5])"],
    5: ["logits = torch.tensor([[-3.0, -1.0, -2.0]])", "logits = torch.tensor([[0.0, 5.0], [9.0, 1.0], [2.0, 3.0]])"],
    6: ["logits = torch.tensor([[1.0, 2.0, 3.0]])", "logits = torch.tensor([[1000.0, 0.0], [0.0, 0.0], [-1.0, 1.0]])"],
    7: ["logits = torch.tensor([[1000.0, -1000.0]])\nlabels = torch.tensor([1])",
        "logits = torch.tensor([[1.0, 1.0, 1.0], [0.0, 2.0, 1.0], [3.0, 0.0, 0.0]])\nlabels = torch.tensor([2, 1, 0])"],
    8: ["logits = torch.tensor([[2.0, 0.0], [0.0, 2.0]])\nlabels = torch.tensor([1.0, 1.0])",
        "logits = torch.tensor([[0.5, 0.0, -0.5]])\nlabels = torch.tensor([2.0])"],
    9: ["logits = torch.tensor([[0.0, 0.0, 0.0]])\nlabels = torch.tensor([2])",
        "logits = torch.tensor([[3.0, 1.0], [1.0, 3.0]])\nlabels = torch.tensor([1, 1])"],
    10: ["logits = torch.tensor([0.0])\ntargets = torch.tensor([0.0])",
         "logits = torch.tensor([[3.0, -3.0], [1.0, -0.5]])\ntargets = torch.tensor([[1.0, 1.0], [0.0, 0.0]])"],
    11: ["logits = torch.tensor([[0.0, 1.0, 2.0]])\nlabels = torch.tensor([2])",
         "logits = torch.tensor([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]])\nlabels = torch.tensor([1, 0, 0, 0])"],
    12: ["logits = torch.tensor([[0.0, 0.0]])\nlabels = torch.tensor([1])\nclass_weights = torch.tensor([1.0, 5.0])",
         "logits = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])\nlabels = torch.tensor([0, 2])\nclass_weights = torch.tensor([2.0, 1.0, 0.5])"],
    13: ["logits = torch.tensor([[0.0, 0.0]])\nlabels = torch.tensor([1])",
         "logits = torch.tensor([[1000.0, 0.0], [1.0, 2.0], [3.0, -1.0]])\nlabels = torch.tensor([0, 0, 1])"],
    14: ["logits = torch.tensor([0.0, 0.0])\ntargets = torch.tensor([1.0, 0.0])\npos_weight = torch.tensor([3.0])",
         "logits = torch.tensor([-2.0])\ntargets = torch.tensor([1.0])\npos_weight = torch.tensor([0.5])"],
    15: ["logits = torch.tensor([[1.0, 0.0], [0.0, 1.0]])\nlabels = torch.tensor([-100, 1])",
         "logits = torch.tensor([[0.0, 3.0, 0.0], [2.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])\nlabels = torch.tensor([1, -100, -100, 2])"],
    16: ["logits = torch.tensor([[0.0, 0.0]])\nlabels = torch.tensor([0])",
         "logits = torch.tensor([[3.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 2.0]])\nlabels = torch.tensor([0, 1])"],
    17: ["pred = torch.tensor([1.0, -1.0])\ntarget = torch.tensor([0.0, 0.0])",
         "pred = torch.tensor([[4.0, 0.25], [0.0, -0.5]])\ntarget = torch.tensor([[0.0, 0.0], [2.0, 0.0]])"],
    18: ["pred = torch.tensor([3.0, 0.0])\ntarget = torch.tensor([1.0, 100.0])\nmask = torch.tensor([1.0, 0.0])",
         "pred = torch.tensor([[1.0, 2.0], [3.0, 4.0]])\ntarget = torch.tensor([[0.0, 0.0], [0.0, 0.0]])\nmask = torch.tensor([[1.0, 0.0], [1.0, 1.0]])"],
}

_PRELUDE = """
import numpy as np
def _np(t):
    return np.asarray(t.tolist(), dtype=np.float64).reshape(tuple(t.shape))
def _f(a):
    return torch.from_numpy(np.array(a, dtype=np.float64, order="C")).to(torch.float32)
def _log_softmax(z):
    m = z.max(axis=1, keepdims=True)
    return z - m - np.log(np.exp(z - m).sum(axis=1, keepdims=True))
def _bce_logits(z, y, pos=1.0):
    log_sig = -np.logaddexp(0, -z)
    log_one_minus = -np.logaddexp(0, z)
    return -(pos * y * log_sig + (1 - y) * log_one_minus)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _f(((_np(pred) - _np(target)) ** 2).mean())",
    2: "expected = _f((_np(pred) - _np(target)) ** 2)",
    3: "expected = _f(((_np(pred) - _np(target)) ** 2).sum())",
    4: "expected = _f(np.abs(_np(pred) - _np(target)).mean())",
    5: "expected = torch.tensor([row.index(max(row)) for row in logits.tolist()], dtype=torch.int64)",
    6: "_z = _np(logits)\nexpected = _f(np.exp(_log_softmax(_z)))",
    7: "_lp = _log_softmax(_np(logits))\nexpected = _f(-np.mean([_lp[i, k] for i, k in enumerate(labels.tolist())]))",
    8: "_lp = _log_softmax(_np(logits))\nexpected = _f(-np.mean([_lp[i, int(k)] for i, k in enumerate(labels.tolist())]))",
    9: "_lp = _log_softmax(_np(logits))\nexpected = _f([-_lp[i, k] for i, k in enumerate(labels.tolist())])",
    10: "expected = _f(_bce_logits(_np(logits), _np(targets)).mean())",
    11: ("_hits = [row.index(max(row)) == k for row, k in zip(logits.tolist(), labels.tolist())]\n"
         "expected = _f(sum(_hits) / len(_hits))"),
    12: ("_lp, _w = _log_softmax(_np(logits)), class_weights.tolist()\n_k = labels.tolist()\n"
         "expected = _f(sum(-_w[k] * _lp[i, k] for i, k in enumerate(_k)) / sum(_w[k] for k in _k))"),
    13: "_lp = _log_softmax(_np(logits))\nexpected = _f(-np.mean([_lp[i, k] for i, k in enumerate(labels.tolist())]))",
    14: "expected = _f(_bce_logits(_np(logits), _np(targets), float(pos_weight[0])).mean())",
    15: ("_lp = _log_softmax(_np(logits))\n_v = [(i, k) for i, k in enumerate(labels.tolist()) if k != -100]\n"
         "expected = _f(-np.mean([_lp[i, k] for i, k in _v]))"),
    16: ("_lp = _log_softmax(_np(logits))\n_c = _lp.shape[1]\n_rows = []\n"
         "for i, k in enumerate(labels.tolist()):\n    _q = np.full(_c, 0.1 / _c)\n    _q[k] += 0.9\n"
         "    _rows.append(-(_q * _lp[i]).sum())\nexpected = _f(np.mean(_rows))"),
    17: ("_e = np.abs(_np(pred) - _np(target))\n"
         "expected = _f(np.where(_e <= 1.0, 0.5 * _e ** 2, 1.0 * (_e - 0.5)).mean())"),
    18: "_m = _np(mask)\nexpected = _f((((_np(pred) - _np(target)) ** 2) * _m).sum() / _m.sum())",
}.items()}

RULES = {
    1: {"required": "call:MSELoss"},
    2: {"required": "call:MSELoss"},
    3: {"required": "call:MSELoss"},
    4: {"required": "call:L1Loss"},
    7: {"required": 'all:["call:CrossEntropyLoss", "not:call:softmax"]'},
    8: {"required": "call:CrossEntropyLoss"},
    9: {"required": "call:CrossEntropyLoss"},
    10: {"required": "call:BCEWithLogitsLoss"},
    12: {"required": "call:CrossEntropyLoss"},
    13: {"required": "call:log_softmax"},
    14: {"required": "call:BCEWithLogitsLoss"},
    15: {"required": "call:CrossEntropyLoss"},
    16: {"required": "call:CrossEntropyLoss"},
    17: {"required": "call:HuberLoss"},
}

WRONG = {
    1: ["result = nn.MSELoss(reduction=\"sum\")(pred, target)", "result = nn.L1Loss()(pred, target)"],
    2: ["result = nn.MSELoss()(pred, target)"],
    3: ["result = nn.MSELoss()(pred, target)"],
    4: ["result = nn.L1Loss(reduction=\"sum\")(pred, target)"],
    5: ["result = logits.argmax(dim=0)", "result = logits.max(dim=1).values"],
    6: ["result = torch.softmax(logits, dim=0)"],
    7: ["result = nn.CrossEntropyLoss()(logits.softmax(dim=1), labels)"],
    8: ["result = nn.CrossEntropyLoss()(logits, labels.long() * 0)"],
    9: ["result = nn.CrossEntropyLoss()(logits, labels)"],
    10: ["result = nn.BCEWithLogitsLoss()(torch.sigmoid(logits), targets)"],
    11: ["result = (logits.argmax(dim=0)[:len(labels)] == labels).float().mean()", "result = (logits.argmax(dim=1) == labels).float().sum()"],
    12: ["result = nn.CrossEntropyLoss()(logits, labels) + 0 * class_weights.sum()",
          "result = nn.CrossEntropyLoss(weight=class_weights, reduction=\"none\")(logits, labels).mean()"],
    13: ["log_probs = torch.log_softmax(logits, dim=0)\npicked = log_probs[torch.arange(len(labels)), labels]\nresult = -picked.mean()",
          "log_probs = torch.log_softmax(logits, dim=1)\npicked = log_probs[torch.arange(len(labels)), labels]\nresult = picked.mean()"],
    14: ["result = nn.BCEWithLogitsLoss()(logits, targets) + 0 * pos_weight.sum()"],
    15: ["result = nn.CrossEntropyLoss(ignore_index=-100, reduction=\"sum\")(logits, labels) / len(labels)"],
    16: ["result = nn.CrossEntropyLoss(label_smoothing=0.0)(logits, labels)"],
    17: ["result = nn.HuberLoss(delta=1.0)(pred, target) * 0 + nn.MSELoss()(pred, target)",
          "result = nn.HuberLoss(delta=2.0)(pred, target)"],
    18: ["per_item = nn.MSELoss(reduction=\"none\")(pred, target)\nresult = (per_item * mask).mean()"],
}


def compile_losses(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
