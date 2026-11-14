"""SK01: reproducible splits. Oracles re-derive the shuffles from
``np.random.RandomState`` and fold-size arithmetic where scikit-learn's
algorithm is documented; stratified and grouped folds use an independent
scikit-learn entry point."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "SK01"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["X = np.arange(16).reshape(8, 2)\ny = np.array([0, 1, 0, 1, 0, 1, 0, 1])",
        "X = np.arange(15).reshape(5, 3)\ny = np.array([1, 0, 1, 0, 1])"],
    2: ["X = np.arange(20).reshape(10, 2) * 10\ny = np.arange(10)",
        "X = np.array([[1.5], [2.5], [3.5], [4.5]])\ny = np.array([0, 1, 0, 1])"],
    3: ["X = np.arange(8).reshape(4, 2)\ny = np.array([7, 6, 5, 4])",
        "X = np.arange(20).reshape(10, 2)\ny = np.arange(20, 30)"],
    4: ["X = np.arange(20).reshape(10, 2)\ny = np.arange(10)",
        "X = np.array([[1.0], [2.0], [3.0]])\ny = np.array([0, 1, 2])"],
    5: ["X = np.arange(8).reshape(4, 2)\ny = np.array([1, 2, 3, 4])",
        "X = np.arange(30).reshape(15, 2)\ny = np.arange(15) * -1"],
    6: ["X = np.arange(20).reshape(10, 2)\ny = np.arange(10, 20)",
        "X = np.arange(6).reshape(3, 2)\ny = np.array([1, 2, 3])"],
    7: ["X = np.arange(24).reshape(12, 2)\ny = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])",
        "X = np.arange(12).reshape(6, 2)\ny = np.array([0, 1, 2, 0, 1, 2])"],
    8: ["X = np.arange(16).reshape(8, 2)\ny = np.array([1, 1, 1, 1, 1, 1, 0, 0])",
        "X = np.arange(40).reshape(20, 2)\ny = np.array([0] * 15 + [1] * 5)"],
    9: ["n = 7", "n = 25"],
    10: ['df = pd.DataFrame({"x": [0.5, 1.5, 2.5, 3.5], "y": [1, 1, 0, 0]}, index=[10, 20, 30, 40])',
         'df = pd.DataFrame({"x": list(range(12)), "y": [0, 1] * 6}, index=[f"r{i}" for i in range(12)])'],
    11: ["X = np.arange(12).reshape(6, 2)", "X = np.arange(10).reshape(10, 1)"],
    12: ["X = np.arange(12).reshape(6, 2)", "X = np.arange(10).reshape(10, 1)"],
    13: ["X = np.arange(12).reshape(6, 2)\ny = np.array([1, 0, 1, 0, 1, 0])",
         "X = np.arange(20).reshape(10, 2)\ny = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1])"],
    14: ["X = np.arange(40).reshape(20, 2)", "X = np.arange(15).reshape(5, 3)"],
    15: ["X = np.arange(12).reshape(6, 2)", "X = np.arange(11).reshape(11, 1)"],
    16: ['X = np.arange(10).reshape(5, 2)\ngroups = np.array(["x", "y", "y", "z", "z"])',
         'X = np.arange(16).reshape(8, 2)\ngroups = np.array(["p", "q", "r", "s", "p", "q", "r", "s"])'],
    17: ["X = np.array([[0.0, 1.0], [2.0, 3.0], [4.0, 5.0], [6.0, 7.0]])",
         "X = np.arange(24, dtype=float).reshape(12, 2) ** 2"],
    18: ["X = np.arange(12).reshape(6, 2)", "X = np.arange(10).reshape(10, 1)"],
}

_PRELUDE = """
import math
def _shuffle_split(n, test_size, seed):
    n_test = math.ceil(test_size * n) if isinstance(test_size, float) else test_size
    perm = np.random.RandomState(seed).permutation(n)
    return perm[n_test:], perm[:n_test]
def _fold_sizes(n, k):
    return [n // k + (1 if i < n % k else 0) for i in range(k)]
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "_n_test = math.ceil(0.25 * len(X))\nexpected = (len(X) - _n_test, _n_test)",
    2: "_tr, _te = _shuffle_split(len(X), 0.25, 42)\nexpected = X[_te]",
    3: "_tr, _te = _shuffle_split(len(X), 2, 0)\nexpected = y[_tr]",
    4: "expected = X[len(X) - math.ceil(0.25 * len(X)):]",
    5: "_tr, _te = _shuffle_split(len(X), 0.3, 3)\nexpected = (X[_tr], y[_tr])",
    6: "_tr, _te = _shuffle_split(len(X), 0.4, 1)\nexpected = y[_te]",
    7: ("from sklearn.model_selection import StratifiedShuffleSplit\n"
        "_tr, _te = next(StratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=7).split(X, y))\n"
        "expected = y[_te]"),
    8: ("from sklearn.model_selection import StratifiedShuffleSplit\n"
        "_tr, _te = next(StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=0).split(X, y))\n"
        "expected = np.array([int((y[_te] == 0).sum()), int((y[_te] == 1).sum())])"),
    9: "_tr, _te = _shuffle_split(n, 0.2, 11)\nexpected = _te.astype(np.int64)",
    10: ("_tr, _te = _shuffle_split(len(df), 0.25, 0)\n"
         "expected = pd.DataFrame({c: [df[c].tolist()[i] for i in _te] for c in df.columns},"
         " index=[list(df.index)[i] for i in _te])"),
    11: ("_sizes, _start, expected = _fold_sizes(len(X), 3), 0, []\n"
         "for _s in _sizes:\n    expected.append(list(range(_start, _start + _s)))\n    _start += _s"),
    12: "_perm = np.random.RandomState(0).permutation(len(X))\nexpected = np.sort(_perm[:_fold_sizes(len(X), 3)[0]]).astype(np.int64)",
    13: ("from sklearn.model_selection import StratifiedKFold as _S\n"
         "expected = [sorted(te.tolist()) for _, te in _S(2).split(np.zeros((len(y), 1)), y)]"),
    14: ("_r, _te = _shuffle_split(len(X), 0.2, 0)\n_rest = X[_r]\n"
         "_tr, _va = _shuffle_split(len(_rest), 0.25, 0)\nexpected = (_rest[_tr], _rest[_va], X[_te])"),
    15: ("_n, _k = len(X), 3\n_t = _n // (_k + 1)\n"
         "expected = [(_n - _t * (_k - i), list(range(_n - _t * (_k - i), _n - _t * (_k - i) + _t))) for i in range(_k)]"),
    16: ("from sklearn.model_selection import GroupKFold as _G\n"
         "expected = [sorted({str(groups[i]) for i in te}) for _, te in _G(2).split(np.zeros((len(groups), 1)), groups=groups)]"),
    17: ("_tr, _te = _shuffle_split(len(X), 0.25, 0)\n"
         "expected = np.array([sum(X[i, j] for i in _tr) / len(_tr) for j in range(X.shape[1])])"),
    18: ("_rng = np.random.RandomState(0)\n_k = math.ceil(0.25 * len(X))\n"
         "expected = [_rng.permutation(len(X))[:_k].tolist() for _ in range(2)]"),
}.items()}

RULES = {
    1: {"required": "call:train_test_split"},
    2: {"required": "call:train_test_split"},
    3: {"required": "call:train_test_split"},
    4: {"required": "call:train_test_split"},
    5: {"required": "call-count:train_test_split:1"},
    6: {"required": "call:train_test_split"},
    7: {"required": "call:train_test_split"},
    8: {"required": "call:bincount"},
    9: {"required": "call:train_test_split"},
    10: {"required": "call:train_test_split"},
    11: {"required": "call:KFold"},
    12: {"required": "call:KFold"},
    13: {"required": "call:StratifiedKFold"},
    15: {"required": "call:TimeSeriesSplit"},
    16: {"required": "call:GroupKFold"},
    18: {"required": "call:ShuffleSplit"},
}

WRONG = {
    1: ["X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)\n"
        "result = (len(X_test), len(X_train))",
        "result = (len(X) - int(len(X) * 0.25), int(len(X) * 0.25))"],
    2: ["result = train_test_split(X, y, test_size=0.25, random_state=42)[0]",
        "result = train_test_split(X, y, test_size=0.25, random_state=0)[1]"],
    3: ["X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=2, random_state=0)\nresult = y_test",
        "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)\nresult = y_train"],
    4: ["result = train_test_split(X, y, test_size=0.25, random_state=0)[1]",
        "result = train_test_split(X, y, test_size=0.25, shuffle=False)[0]"],
    5: ["a = train_test_split(X, test_size=0.3, random_state=3)[0]\nb = train_test_split(y, test_size=0.3, random_state=4)[0]\n"
        "result = (a, b)"],
    6: ["X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=1)\nresult = y_train"],
    7: ["result = train_test_split(X, y, test_size=0.5, random_state=7)[3]"],
    8: ["X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)\n"
        "result = np.bincount(y_test, minlength=2)",
        "result = np.bincount(y, minlength=2)"],
    9: ["result = train_test_split(np.arange(n), test_size=0.2, random_state=11)[0]"],
    10: ["result = train_test_split(df, test_size=0.25, random_state=0)[1].reset_index(drop=True)"],
    11: ["result = [train.tolist() for train, test in KFold(n_splits=3).split(X)]"],
    12: ["train, test = next(iter(KFold(n_splits=3).split(X)))\nresult = test"],
    13: ["from sklearn.model_selection import KFold\nresult = [test.tolist() for train, test in KFold(n_splits=2).split(X)]"],
    14: ["X_rest, X_test = train_test_split(X, test_size=0.2, random_state=0)\n"
         "X_train, X_val = train_test_split(X, test_size=0.25, random_state=0)\nresult = (X_train, X_val, X_test)"],
    15: ["from sklearn.model_selection import KFold\n"
         "result = [(len(train), test.tolist()) for train, test in KFold(n_splits=3).split(X)]"],
    16: ["from sklearn.model_selection import KFold\n"
         "result = [sorted(set(groups[test].tolist())) for train, test in KFold(n_splits=2).split(X)]"],
    17: ["result = X.mean(axis=0)"],
    18: ["splitter = ShuffleSplit(n_splits=2, test_size=0.25, random_state=0)\n"
         "result = [sorted(test.tolist()) for train, test in splitter.split(X)]"],
}


def compile_splitting(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
