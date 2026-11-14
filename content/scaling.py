"""SK02: fitting preprocessing on training data only, Pipeline and friends.

Oracles use NumPy formulas (and least squares for linear models) instead of the
scikit-learn transformers they check."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "SK02"
LESSONS = load_lessons(__file__)

CONST = "train = np.array([[2.0, 5.0, 1.0], [2.0, 1.0, 3.0]])"

ALTERNATIVES = {
    1: [CONST, "train = np.array([[0.0], [1.0], [2.0], [3.0]])"],
    2: [CONST + "\ntest = np.array([[0.0, 0.0, 0.0]])",
        "train = np.array([[10.0], [20.0]])\ntest = np.array([[15.0], [30.0], [0.0]])"],
    3: [CONST + "\ntest = np.array([[3.0, 3.0, 2.0]])",
        "train = np.array([[-1.0], [1.0]])\ntest = np.array([[0.0], [2.0], [-3.0]])"],
    4: ["train = np.array([[1.0], [2.0], [6.0]])\ntest = np.array([[0.0], [0.0]])",
        "train = np.array([[5.0, -5.0, 0.0], [7.0, -1.0, 0.0]])\ntest = np.array([[9.0, 9.0, 9.0]])"],
    5: [CONST, "train = np.array([[1.0], [2.0], [3.0], [4.0]])"],
    6: [CONST, "train = np.array([[0.0, 1.0], [4.0, 1.0]])"],
    7: [CONST + "\ntest = np.array([[1.0, 2.0, 3.0]])",
        "train = np.array([[10.0], [20.0]])\ntest = np.array([[-5.0], [12.5]])"],
    8: [CONST + "\ntest = np.array([[0.0, 0.0, 0.0]])",
        "train = np.array([[10.0], [20.0]])\ntest = np.array([[15.0], [30.0], [0.0]])"],
    9: [CONST + "\ntest = np.array([[4.0, 4.0, 4.0]])",
        "train = np.array([[-2.0], [2.0]])\ntest = np.array([[1.0], [-6.0]])"],
    10: [CONST + "\ntest = np.array([[2.0, 3.0, 2.0]])",
         "train = np.array([[-1.0], [3.0]])\ntest = np.array([[0.0], [5.0]])"],
    11: ["X_train = np.array([[0.0], [1.0], [2.0]])\ny_train = np.array([1.0, 3.0, 5.0])\nX_test = np.array([[10.0]])",
         "X_train = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0]])\ny_train = np.array([2.0, -1.0, 1.0, 4.0])\n"
         "X_test = np.array([[0.0, 0.0], [3.0, 3.0]])"],
    12: ["X = np.array([[1.0], [3.0]])\ny = np.array([0.0, 1.0])",
         "X = np.array([[0.0, 0.0, 9.0], [6.0, 2.0, 9.0], [3.0, 1.0, 9.0], [3.0, 5.0, 9.0]])\ny = np.array([1.0, 2.0, 3.0, 4.0])"],
    13: ['df = pd.DataFrame({"x2": [0.0, 2.0], "x1": [5.0, 5.0], "name": ["p", "q"]})',
         'df = pd.DataFrame({"name": ["a", "b", "c", "d"], "x1": [0.0, 1.0, 2.0, 3.0], "x2": [4.0, 0.0, 0.0, 4.0]})'],
    14: ['train = np.array([["b"], ["a"]])\ntest = np.array([["a"], ["a"], ["b"], ["z"]])',
         'train = np.array([["dog"], ["cat"], ["owl"]])\ntest = np.array([["owl"]])'],
    15: ["train = np.array([[2.0], [np.nan], [4.0]])\ntest = np.array([[np.nan], [1.0]])",
         "train = np.array([[1.0, 2.0, np.nan], [5.0, np.nan, 3.0]])\ntest = np.array([[np.nan, np.nan, np.nan]])"],
    16: ["train = np.array([[2.0], [np.nan], [4.0]])\ntest = np.array([[np.nan], [6.0]])",
         "train = np.array([[1.0, 0.0], [3.0, np.nan], [np.nan, 4.0], [4.0, 2.0]])\ntest = np.array([[np.nan, np.nan]])"],
    17: ["X = np.array([[0.0], [1.0], [5.0], [6.0], [2.0], [7.0]])\ny = np.array([0, 0, 1, 1, 0, 1])",
         "X = np.array([[0.0], [9.0], [1.0], [8.0], [2.0], [7.0], [3.0], [6.0], [4.5], [4.0]])\n"
         "y = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])"],
    18: ["X = np.array([[0.0], [1.0], [2.0]])\ny = np.array([1.0, 3.0, 5.0])",
         "X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0]])\ny = np.array([2.0, -1.0, 1.0, 4.0])"],
}

_PRELUDE = """
def _stats(a):
    mu = np.nanmean(a, axis=0)
    sd = np.sqrt(np.nanmean((a - mu) ** 2, axis=0))
    return mu, np.where(sd == 0, 1.0, sd)
def _minmax(a):
    lo, hi = a.min(axis=0), a.max(axis=0)
    return lo, np.where(hi - lo == 0, 1.0, hi - lo)
def _lstsq(a, b):
    design = np.hstack([a, np.ones((len(a), 1))])
    w = np.linalg.lstsq(design, b, rcond=None)[0]
    return w[:-1], w[-1]
def _impute(fit, data):
    mu = np.nanmean(fit, axis=0)
    return np.where(np.isnan(data), mu, data)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "_m, _s = _stats(train)\nexpected = (train - _m) / _s",
    2: "_m, _s = _stats(train)\nexpected = (test - _m) / _s",
    3: "_lo, _r = _minmax(train)\nexpected = (test - _lo) / _r",
    4: "expected = np.array([sum(c) / len(c) for c in train.T.tolist()])",
    5: "_m = train.mean(axis=0)\nexpected = ((train - _m) ** 2).mean(axis=0)",
    6: "expected = _stats(train)[1]",
    7: "expected = test.astype(np.float64)",
    8: "_m, _s = _stats(train)\nexpected = (test - _m) / _s",
    9: "expected = test / _stats(train)[1]",
    10: "_lo, _r = _minmax(train)\nexpected = (test - _lo) / _r * 2 - 1",
    11: "_w, _b = _lstsq(X_train, y_train)\nexpected = X_test @ _w + _b",
    12: "expected = X.mean(axis=0)",
    13: "_a = df[['x1', 'x2']].to_numpy(dtype=float)\n_m, _s = _stats(_a)\nexpected = (_a - _m) / _s",
    14: ("_cats = sorted(set(train.ravel().tolist()))\n"
         "expected = np.array([[1.0 if v == c else 0.0 for c in _cats] for v in test.ravel().tolist()])"),
    15: "expected = _impute(train, test)",
    16: "_t = _impute(train, train)\n_m, _s = _stats(_t)\nexpected = (_impute(train, test) - _m) / _s",
    17: ("from sklearn.model_selection import StratifiedKFold as _S\n"
         "from sklearn.linear_model import LogisticRegression as _L\n_scores = []\n"
         "for _tr, _te in _S(2).split(X, y):\n    _m, _s = _stats(X[_tr])\n"
         "    _model = _L().fit((X[_tr] - _m) / _s, y[_tr])\n"
         "    _scores.append(float(np.mean(_model.predict((X[_te] - _m) / _s) == y[_te])))\n"
         "expected = np.array(_scores)"),
    18: "_w, _b = _lstsq(X, y)\nexpected = _w * _stats(X)[1]",
}.items()}

RULES = {
    1: {"required": "call:StandardScaler"},
    2: {"required": "call:StandardScaler"},
    3: {"required": "call:MinMaxScaler"},
    4: {"required": "attr:mean_"},
    5: {"required": "attr:var_"},
    6: {"required": "attr:scale_"},
    7: {"required": "call:inverse_transform"},
    8: {"required": "call:Pipeline"},
    9: {"required": "call:StandardScaler"},
    10: {"required": "call:MinMaxScaler"},
    11: {"required": "call:Pipeline"},
    12: {"required": "attr:named_steps"},
    13: {"required": "call:ColumnTransformer"},
    14: {"required": "call:OneHotEncoder"},
    15: {"required": "call:SimpleImputer"},
    16: {"required": "call:Pipeline"},
    17: {"required": "call:cross_val_score"},
    18: {"required": "attr:named_steps"},
}

WRONG = {
    1: ["result = StandardScaler().fit_transform(train.T).T", "result = train - train.mean(axis=0)"],
    2: ["result = StandardScaler().fit_transform(test)", "scaler = StandardScaler().fit(np.vstack([train, test]))\nresult = scaler.transform(test)"],
    3: ["result = MinMaxScaler().fit_transform(test)", "result = np.clip(MinMaxScaler().fit(train).transform(test), 0, 1)"],
    4: ["result = StandardScaler().fit(np.vstack([train, test])).mean_"],
    5: ["result = StandardScaler().fit(train).scale_", "s = StandardScaler().fit(train)\nresult = s.var_ * len(train) / (len(train) - 1)"],
    6: ["result = train.std(axis=0)"],
    7: ["scaler = StandardScaler().fit(train)\nresult = scaler.inverse_transform(test)"],
    8: ['pipe = Pipeline([("scale", StandardScaler())])\nresult = pipe.fit_transform(test)'],
    9: ["result = StandardScaler().fit(train).transform(test)"],
    10: ["result = MinMaxScaler().fit(train).transform(test)"],
    11: ['pipe = Pipeline([("scale", StandardScaler()), ("model", LinearRegression())])\n'
         'pipe.fit(X_train, y_train)\nresult = pipe.predict(X_train)'],
    12: ['pipe = make_pipeline(StandardScaler(), LinearRegression()).fit(X, y)\nresult = pipe.named_steps["standardscaler"].scale_'],
    13: ['ct = ColumnTransformer([("num", StandardScaler(), ["x1", "x2"])], remainder="drop")\nresult = ct.fit_transform(df)[:, ::-1]',
         'ct = ColumnTransformer([("num", StandardScaler(), ["x2", "x1"])], remainder="drop")\nresult = ct.fit_transform(df)'],
    14: ['encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(test)\nresult = encoder.transform(test)'],
    15: ['result = SimpleImputer(strategy="mean").fit_transform(test)', 'result = SimpleImputer(strategy="median").fit(train).transform(test)'],
    16: ['pipe = Pipeline([("impute", SimpleImputer(strategy="mean")), ("scale", StandardScaler())])\nresult = pipe.fit_transform(test)'],
    17: ["Xs = StandardScaler().fit_transform(X)\nresult = cross_val_score(LogisticRegression(), Xs, y, cv=3)"],
    18: ['pipe = Pipeline([("model", LinearRegression())]).fit(X, y)\nresult = pipe.named_steps["model"].coef_'],
}


def compile_scaling(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
