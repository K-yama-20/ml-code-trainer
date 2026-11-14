"""SK03: fit, predict, probabilities and learned attributes.

Linear models are checked against closed-form least squares. Logistic
regression has no closed form, so its oracle refits the model and recomputes
probabilities and labels by hand from ``coef_`` and ``intercept_``."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "SK03"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ["X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])\ny = np.array([3.0, 5.0, 8.0])\nX_test = np.array([[2.0, 2.0]])",
        "X = np.array([[0.0], [2.0]])\ny = np.array([4.0, 0.0])\nX_test = np.array([[1.0], [3.0], [-1.0]])"],
    2: ["X = np.array([[0.0], [1.0], [2.0]])\ny = np.array([5.0, 3.0, 1.0])",
        "X = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 1.0, 1.0], [2.0, 0.0, 1.0]])\n"
        "y = np.array([1.0, 2.0, 3.0, 6.0, 5.0])"],
    3: ["X = np.array([[0.0], [1.0], [2.0]])\ny = np.array([5.0, 3.0, 1.0])",
        "X = np.array([[1.0], [2.0], [3.0], [4.0]])\ny = np.array([-1.0, -2.0, -3.0, -4.0])"],
    4: ["X = np.array([[0.0, 0.0], [1.0, 1.0], [5.0, 5.0], [6.0, 6.0]])\ny = np.array([1, 1, 0, 0])\n"
        "X_test = np.array([[5.5, 5.0], [0.0, 1.0]])",
        "X = np.array([[0.0], [1.0], [9.0], [10.0]])\ny = np.array([2, 2, 7, 7])\nX_test = np.array([[10.0], [8.0], [2.0], [0.0]])"],
    5: ["X = np.array([[0.0], [1.0], [2.0], [3.0]])\ny = np.array([1, 1, 0, 0])\nX_test = np.array([[1.5], [0.0]])",
        "X = np.array([[0.0, 1.0], [1.0, 0.0], [2.0, 3.0], [3.0, 2.0]])\ny = np.array([0, 0, 1, 1])\n"
        "X_test = np.array([[1.0, 1.0], [2.0, 2.0], [4.0, 4.0]])"],
    6: ["X = np.array([[0.0], [1.0], [5.0], [6.0], [10.0], [11.0]])\ny = np.array([0, 0, 1, 1, 2, 2])\nX_test = np.array([[3.0]])",
        "X = np.array([[0.0], [1.0], [2.0], [3.0]])\ny = np.array([0, 1, 0, 1])\n"
        "X_test = np.array([[0.0], [1.0], [2.0], [3.0], [4.0]])"],
    7: ['X = np.array([[0.0], [1.0], [5.0], [6.0], [10.0], [11.0]])\ny = np.array(["c", "c", "a", "a", "b", "b"])',
        'X = np.array([[0.0], [1.0], [8.0], [9.0]])\ny = np.array(["spam", "ham", "spam", "ham"])'],
    8: ['X = np.array([[0.0], [1.0], [2.0], [7.0], [8.0], [9.0]])\ny = np.array(["dog", "dog", "dog", "cat", "cat", "cat"])\n'
        'X_test = np.array([[1.5], [6.0]])\ntarget = "dog"',
        'X = np.array([[0.0], [1.0], [3.0], [4.0]])\ny = np.array(["a", "a", "b", "b"])\nX_test = np.array([[2.0], [0.0]])\ntarget = "b"'],
    9: ["probabilities = np.array([[0.49, 0.51], [0.51, 0.49]])",
        "probabilities = np.array([[0.0, 1.0], [1.0, 0.0], [0.25, 0.75], [0.9, 0.1]])"],
    10: ["X = np.array([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0]])\ny = np.array([0, 0, 0, 1, 1, 1])\n"
         "X_test = np.array([[1.0], [2.0], [3.0], [4.0]])\nthreshold = 0.7",
         "X = np.array([[0.0], [1.0], [2.0], [3.0]])\ny = np.array([0, 1, 0, 1])\nX_test = np.array([[0.0], [3.0]])\nthreshold = 0.5"],
    11: ["X_train = np.array([[0.0], [1.0], [2.0]])\ny_train = np.array([1.0, 1.0, 1.0])\n"
         "X_test = np.array([[0.0], [1.0]])\ny_test = np.array([0.0, 2.0])",
         "X_train = np.array([[0.0], [2.0]])\ny_train = np.array([0.0, 4.0])\nX_test = np.array([[1.0], [3.0], [5.0]])\n"
         "y_test = np.array([2.0, 6.0, 10.0])"],
    12: ["X = np.array([[0.0], [1.0], [4.0], [5.0]])\ny = np.array([0, 0, 1, 1])\nX_test = np.array([[2.5], [-1.0]])",
         "X = np.array([[0.0, 0.0], [0.0, 1.0], [3.0, 0.0], [3.0, 1.0]])\ny = np.array([1, 1, 0, 0])\nX_test = np.array([[1.0, 1.0]])"],
    13: ["X = np.array([[0.0, 0.0], [0.0, 1.0], [5.0, 5.0], [5.0, 6.0], [6.0, 5.0]])\ny = np.array([1, 1, 0, 0, 0])\n"
         "X_test = np.array([[0.0, 0.4], [5.0, 4.0]])",
         "X = np.array([[0.0], [1.0], [2.0], [10.0]])\ny = np.array([3, 3, 4, 4])\nX_test = np.array([[0.9], [8.0], [1.8]])"],
    14: ["X = np.array([[0.0], [1.0]])\ny = np.array([0.0, 2.0])",
         "X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])\ny = np.array([1.0, 2.0, 3.0, 4.0])"],
    15: ["X = np.array([[0.0], [1.0], [5.0], [6.0], [10.0], [11.0]])\ny = np.array([3, 3, 1, 1, 2, 2])\n"
         "X_test = np.array([[11.0], [0.0]])",
         "X = np.array([[0.0], [1.0], [8.0], [9.0]])\ny = np.array([-1, -1, 5, 5])\nX_test = np.array([[0.0], [9.0], [1.0]])"],
    16: ["X_train = np.array([[0.0], [10.0]])\ny_train = np.array([0, 1])\nX_test = np.array([[1.0], [9.0], [6.0]])\n"
         "y_test = np.array([0, 1, 0])",
         "X_train = np.array([[0.0], [1.0], [2.0]])\ny_train = np.array([1, 1, 1])\nX_test = np.array([[5.0]])\ny_test = np.array([0])"],
    17: ["X1 = np.array([[0.0], [1.0]])\ny1 = np.array([9.0, 9.0])\nX2 = np.array([[0.0], [2.0], [4.0]])\n"
         "y2 = np.array([0.0, 1.0, 2.0])\nX_test = np.array([[6.0], [0.0]])",
         "X1 = np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])\ny1 = np.array([1.0, 2.0, 3.0])\n"
         "X2 = np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])\ny2 = np.array([3.0, 2.0, 1.0])\nX_test = np.array([[2.0, 2.0]])"],
    18: ["X = np.array([[0.0], [1.0], [2.0]])\ny = np.array([0.0, 3.0, 0.0])\nweights = np.array([1.0, 2.0, 1.0])\n"
         "X_test = np.array([[1.0], [3.0]])",
         "X = np.array([[0.0], [1.0], [2.0], [3.0]])\ny = np.array([1.0, 0.0, 5.0, 7.0])\nweights = np.array([0.0, 0.0, 1.0, 1.0])\n"
         "X_test = np.array([[0.0]])"],
}

_PRELUDE = """
import math
from sklearn.linear_model import LogisticRegression as _LR
def _lstsq(a, b, w=None):
    design = np.hstack([a, np.ones((len(a), 1))])
    if w is not None:
        root = np.sqrt(w)[:, None]
        design, b = design * root, b * root[:, 0]
    coef = np.linalg.lstsq(design, b, rcond=None)[0]
    return coef[:-1], coef[-1]
def _sigmoid(z):
    return np.array([1 / (1 + math.exp(-v)) for v in np.ravel(z).tolist()])
def _logistic(a, b, test):
    m = _LR().fit(a, b)
    scores = test @ m.coef_.T + m.intercept_
    return sorted(set(b.tolist())), scores
def _knn(train, labels, test, k):
    out = []
    for t in test:
        order = sorted(range(len(train)), key=lambda i: (float(np.sum((train[i] - t) ** 2)), i))[:k]
        votes = [labels[i] for i in order]
        out.append(max(sorted(set(votes)), key=votes.count))
    return np.array(out)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "_w, _b = _lstsq(X, y)\nexpected = X_test @ _w + _b",
    2: "expected = _lstsq(X, y)[0]",
    3: "expected = float(_lstsq(X, y)[1])",
    4: "_c, _s = _logistic(X, y, X_test)\nexpected = np.array([_c[1] if v > 0 else _c[0] for v in _s[:, 0]])",
    5: "_c, _s = _logistic(X, y, X_test)\nexpected = _sigmoid(_s[:, 0])",
    6: "expected = (len(X_test), len(set(y.tolist())))",
    7: "expected = np.array(sorted(set(y.tolist())))",
    8: ("_c, _s = _logistic(X, y, X_test)\n_p1 = _sigmoid(_s[:, 0])\n"
        "expected = _p1 if _c.index(target) == 1 else 1 - _p1"),
    9: "expected = np.array([1 if p >= 0.5 else 0 for p in probabilities[:, 1].tolist()], dtype=np.int64)",
    10: ("_c, _s = _logistic(X, y, X_test)\n"
         "expected = np.array([1 if p >= threshold else 0 for p in _sigmoid(_s[:, 0])], dtype=np.int64)"),
    11: ("_w, _b = _lstsq(X_train, y_train)\n_pred = X_test @ _w + _b\n"
         "expected = float(1 - np.sum((y_test - _pred) ** 2) / np.sum((y_test - y_test.mean()) ** 2))"),
    12: "_c, _s = _logistic(X, y, X_test)\nexpected = _s[:, 0]",
    13: "expected = _knn(X, y, X_test, 3)",
    14: ("_xc, _yc = X - X.mean(axis=0), y - y.mean()\n"
         "expected = np.linalg.solve(_xc.T @ _xc + 1.0 * np.eye(X.shape[1]), _xc.T @ _yc)"),
    15: ("_c, _s = _logistic(X, y, X_test)\n_e = np.exp(_s - _s.max(axis=1, keepdims=True))\n"
         "if _s.shape[1] == 1:\n    expected = np.array([_c[1] if v > 0 else _c[0] for v in _s[:, 0]])\n"
         "else:\n    expected = np.array([_c[i] for i in (_e / _e.sum(axis=1, keepdims=True)).argmax(axis=1)])"),
    16: ("expected = (float(np.mean(_knn(X_train, y_train, X_train, 1) == y_train)),"
         " float(np.mean(_knn(X_train, y_train, X_test, 1) == y_test)))"),
    17: "_w, _b = _lstsq(X2, y2)\nexpected = X_test @ _w + _b",
    18: "_w, _b = _lstsq(X, y, weights)\nexpected = X_test @ _w + _b",
}.items()}

RULES = {
    1: {"required": "call:LinearRegression"},
    2: {"required": "attr:coef_"},
    3: {"required": "attr:intercept_"},
    4: {"required": "call:LogisticRegression"},
    5: {"required": "call:predict_proba"},
    6: {"required": "call:predict_proba"},
    7: {"required": "attr:classes_"},
    8: {"required": "call:predict_proba"},
    9: {"dtype": True},
    10: {"required": "call:predict_proba", "dtype": True},
    11: {"required": "call:score"},
    12: {"required": "call:decision_function"},
    13: {"required": "call:KNeighborsClassifier"},
    14: {"required": "call:Ridge"},
    15: {"required": "call:predict_proba"},
    16: {"required": "call:score"},
    17: {"required": "call-count:fit:2"},
}

WRONG = {
    1: ["model = LinearRegression().fit(X, y)\nresult = model.predict(X)"],
    2: ["result = LinearRegression().fit(X, y).coef_[::-1]",
        "result = LinearRegression(fit_intercept=False).fit(X, y).coef_"],
    3: ["result = float(LinearRegression().fit(X, y).coef_[0])"],
    4: ["model = LogisticRegression().fit(X, y)\nresult = model.predict(X)",
        "model = LogisticRegression().fit(X, y)\nresult = model.predict_proba(X_test)[:, 1]"],
    5: ["model = LogisticRegression().fit(X, y)\nresult = model.predict_proba(X_test)[:, 0]",
        "model = LogisticRegression().fit(X, y)\nresult = model.predict_proba(X_test).max(axis=1)"],
    6: ["model = LogisticRegression().fit(X, y)\nresult = model.predict_proba(X).shape"],
    7: ["result = np.array(list(dict.fromkeys(y.tolist())))"],
    8: ["model = LogisticRegression().fit(X, y)\nresult = model.predict_proba(X_test)[:, 1]"],
    9: ["result = probabilities.argmax(axis=1).astype(np.int64)", "result = (probabilities[:, 1] >= 0.5)"],
    10: ["model = LogisticRegression().fit(X, y)\nresult = model.predict(X_test).astype(np.int64)"],
    11: ["model = LinearRegression().fit(X_train, y_train)\nresult = model.score(X_train, y_train)"],
    12: ["model = LogisticRegression().fit(X, y)\nresult = model.predict_proba(X_test)[:, 1]"],
    13: ["from sklearn.neighbors import KNeighborsClassifier as K\nresult = K(n_neighbors=1).fit(X, y).predict(X_test)"],
    14: ["result = Ridge(alpha=10.0).fit(X, y).coef_"],
    15: ["model = LogisticRegression().fit(X, y)\nproba = model.predict_proba(X_test)\nresult = proba.argmax(axis=1)"],
    16: ["model = KNeighborsClassifier(n_neighbors=1).fit(X_train, y_train)\n"
         "result = (model.score(X_test, y_test), model.score(X_train, y_train))"],
    17: ["model = LinearRegression()\nmodel.fit(X2, y2)\nmodel.fit(X1, y1)\nresult = model.predict(X_test)"],
    18: ["model = LinearRegression().fit(X, y)\nresult = model.predict(X_test)"],
}


def compile_estimators(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
