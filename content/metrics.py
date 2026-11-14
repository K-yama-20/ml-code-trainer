"""SK04: classification and regression metrics, computed by hand in oracles."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "SK04"
LESSONS = load_lessons(__file__)


def lists(**values):
    return "\n".join(f"{k} = {v!r}" for k, v in values.items())


ALTERNATIVES = {
    1: [lists(truth=[1], pred=[1]), lists(truth=[0, 0, 1, 1], pred=[1, 1, 0, 1])],
    2: [lists(truth=[1, 1, 0], pred=[1, 1, 0]), lists(truth=[0, 0, 1, 1], pred=[1, 1, 1, 0])],
    3: [lists(truth=[1, 1, 1, 1], pred=[1, 0, 0, 0]), lists(truth=[0, 1, 1], pred=[1, 1, 1])],
    4: [lists(truth=[1, 1, 0, 0], pred=[1, 0, 1, 0]), lists(truth=[1, 0, 1], pred=[0, 0, 0])],
    5: [lists(truth=[0.0, 0.0], pred=[1.0, -3.0]), lists(truth=[10.0], pred=[7.5])],
    6: [lists(truth=[0.0, 0.0], pred=[1.0, -3.0]), lists(truth=[10.0], pred=[7.5])],
    7: [lists(truth=[1, 1, 1], pred=[1, 1, 1]), lists(truth=[0, 1, 0, 1], pred=[1, 1, 1, 0])],
    8: [lists(truth=[1, 1], pred=[0, 1]), lists(truth=[0, 0, 0, 1, 1], pred=[1, 1, 0, 1, 1])],
    9: [lists(truth=[0, 0, 0], pred=[0, 0, 1]), lists(truth=[1, 0, 1, 0], pred=[1, 0, 1, 0])],
    10: [lists(truth=[0, 1, 2], pred=[0, 1, 2]), lists(truth=[0, 0, 1, 1, 2, 2], pred=[0, 1, 1, 1, 1, 0])],
    11: [lists(truth=[1.0, 2.0, 3.0], pred=[3.0, 2.0, 1.0]), lists(truth=[0.0, 10.0], pred=[1.0, 9.0])],
    12: [lists(truth=["ham", "spam"], pred=["spam", "spam"]), lists(truth=["spam", "spam", "ham"], pred=["spam", "ham", "ham"])],
    13: ["truth = []\npred = []", "truth = np.array([3, 3, 1])\npred = np.array([1, 3, 3])"],
    14: [lists(truth=[0, 1], scores=[0.9, 0.1]), lists(truth=[1, 0, 1, 0], scores=[0.5, 0.5, 0.7, 0.2])],
    15: ["truth = np.array([1, 1, 0])\nproba = np.array([0.3, 0.8, 0.1])\nthreshold = 0.25",
         "truth = np.array([0, 1, 0, 1])\nproba = np.array([0.5, 0.49, 0.7, 0.9])\nthreshold = 0.5"],
    16: [lists(truth=[0, 1, 1, 1], pred=[0, 1, 1, 1]), lists(truth=[0, 0, 1, 1, 1, 1], pred=[1, 0, 1, 0, 0, 1])],
    17: [lists(truth=[0.0, 0.0], pred=[1.0, -3.0]), lists(truth=[10.0], pred=[7.5])],
    18: [lists(truth=[1, 0], pred=[0, 0]), lists(truth=[1, 1, 1, 0], pred=[1, 1, 0, 0])],
}

_PRELUDE = """
import numpy as np
import math
def _counts(t, p, positive=1):
    tp = sum(1 for a, b in zip(t, p) if a == positive and b == positive)
    fp = sum(1 for a, b in zip(t, p) if a != positive and b == positive)
    fn = sum(1 for a, b in zip(t, p) if a == positive and b != positive)
    tn = sum(1 for a, b in zip(t, p) if a != positive and b != positive)
    return tp, fp, fn, tn
def _div(a, b):
    return a / b if b else 0.0
def _prf(t, p, positive=1):
    tp, fp, fn, _ = _counts(t, p, positive)
    prec, rec = _div(tp, tp + fp), _div(tp, tp + fn)
    return prec, rec, _div(2 * prec * rec, prec + rec)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = sum(a == b for a, b in zip(truth, pred)) / len(truth)",
    2: "expected = _prf(truth, pred)[0]",
    3: "expected = _prf(truth, pred)[1]",
    4: "expected = _prf(truth, pred)[2]",
    5: "expected = sum(abs(a - b) for a, b in zip(truth, pred)) / len(truth)",
    6: "expected = sum((a - b) ** 2 for a, b in zip(truth, pred)) / len(truth)",
    7: "expected = np.array([[sum(1 for a, b in zip(truth, pred) if a == i and b == j) for j in (0, 1)] for i in (0, 1)])",
    8: "_tp, _fp, _fn, _tn = _counts(truth, pred)\nexpected = (_tn, _fp, _fn, _tp)",
    9: "expected = np.array([_prf(truth, pred, c)[2] for c in (0, 1)])",
    10: "_cls = sorted(set(truth) | set(pred))\nexpected = sum(_prf(truth, pred, c)[2] for c in _cls) / len(_cls)",
    11: ("_m = sum(truth) / len(truth)\n"
         "expected = 1 - sum((a - b) ** 2 for a, b in zip(truth, pred)) / sum((a - _m) ** 2 for a in truth)"),
    12: "expected = _prf(truth, pred, 'spam')[0]",
    13: "expected = sum(1 for a, b in zip(list(truth), list(pred)) if a != b)",
    14: ("_pos = [s for t, s in zip(truth, scores) if t == 1]\n_neg = [s for t, s in zip(truth, scores) if t == 0]\n"
         "expected = sum(1.0 if p > q else 0.5 if p == q else 0.0 for p in _pos for q in _neg) / (len(_pos) * len(_neg))"),
    15: ("_pred = [1 if v >= threshold else 0 for v in proba.tolist()]\n"
         "expected = sum(a == b for a, b in zip(truth.tolist(), _pred)) / len(_pred)"),
    16: "_cls = sorted(set(truth))\nexpected = sum(_prf(truth, pred, c)[1] for c in _cls) / len(_cls)",
    17: "expected = math.sqrt(sum((a - b) ** 2 for a, b in zip(truth, pred)) / len(truth))",
    18: "_p, _r, _f = _prf(truth, pred)\nexpected = {'precision': _p, 'recall': _r, 'f1': _f}",
}.items()}

RULES = {
    1: {"required": "call:accuracy_score"},
    2: {"required": "call:precision_score"},
    3: {"required": "call:recall_score"},
    4: {"required": "call:f1_score"},
    5: {"required": "call:mean_absolute_error"},
    6: {"required": "call:mean_squared_error"},
    7: {"required": "call:confusion_matrix"},
    8: {"required": "call:confusion_matrix"},
    9: {"required": "call:f1_score"},
    10: {"required": "call:f1_score"},
    11: {"required": "call:r2_score"},
    12: {"required": "call:precision_score"},
    14: {"required": "call:roc_auc_score"},
    15: {"required": "call:accuracy_score"},
    16: {"required": "call:balanced_accuracy_score"},
}

WRONG = {
    1: ["result = sum(a == b for a, b in zip(truth, pred))"],
    2: ["result = precision_score(truth, pred, pos_label=0)",
        "result = precision_score(pred, truth)"],
    3: ["result = recall_score(pred, truth)"],
    4: ["result = f1_score(truth, pred, zero_division=1)", 'result = f1_score(truth, pred, average="macro", zero_division=0)'],
    5: ["result = mean_absolute_error(truth, pred) ** 2"],
    6: ["result = mean_squared_error(truth, pred) ** 0.5"],
    7: ["result = confusion_matrix(pred, truth, labels=[0, 1])", "result = confusion_matrix(truth, pred)"],
    8: ["matrix = confusion_matrix(truth, pred, labels=[0, 1])\nresult = tuple(int(v) for v in matrix.ravel()[::-1])"],
    9: ["result = f1_score(truth, pred, labels=[1, 0], average=None, zero_division=0)"],
    10: ['result = f1_score(truth, pred, average="weighted", zero_division=0)',
         'result = f1_score(truth, pred, average="micro", zero_division=0)'],
    11: ["result = r2_score(pred, truth)"],
    12: ['result = precision_score(truth, pred, pos_label="ham")'],
    13: ["result = int(np.count_nonzero(np.asarray(truth) == np.asarray(pred)))"],
    14: ["result = roc_auc_score(truth, [1 if s >= 0.5 else 0 for s in scores])"],
    15: ["pred = (proba > threshold).astype(int)\nresult = accuracy_score(truth, pred)",
         "pred = (proba >= 0.5).astype(int)\nresult = accuracy_score(truth, pred)"],
    16: ["result = balanced_accuracy_score(pred, truth)"],
    17: ["from sklearn.metrics import mean_absolute_error\nresult = mean_absolute_error(truth, pred)",
         "result = mean_squared_error(truth, pred)"],
    18: ["result = {\n    \"precision\": recall_score(truth, pred, zero_division=0),\n"
         "    \"recall\": precision_score(truth, pred, zero_division=0),\n    \"f1\": f1_score(truth, pred, zero_division=0),\n}"],
}


def compile_metrics(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
