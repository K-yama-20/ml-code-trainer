"""PD02: detecting, dropping and filling missing values."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PD02"
LESSONS = load_lessons(__file__)

ALTERNATIVES = {
    1: ['df = pd.DataFrame({"value": [2.0, 4.0], "score": [np.nan, np.nan]})',
        'df = pd.DataFrame({"value": [np.nan, np.nan, np.nan], "score": [1.0, 2.0, 3.0]})'],
    2: ['df = pd.DataFrame({"score": [1.0, 2.0], "value": [3.0, 4.0]})',
        'df = pd.DataFrame({"a": [np.nan, np.nan, np.nan], "b": [1.0, np.nan, 2.0]})'],
    3: ['df = pd.DataFrame({"value": [np.nan, 2.0, np.nan], "score": [1, 2, 3]}, index=[10, 20, 30])',
        'df = pd.DataFrame({"value": [1.0, 2.0], "score": [5, 6]}, index=["x", "y"])'],
    4: ['df = pd.DataFrame({"value": [np.nan, np.nan], "score": [1.0, 2.0]}, index=[5, 6])',
        'df = pd.DataFrame({"score": [np.nan, 3.0, 4.0], "value": [7.0, np.nan, 8.0]})'],
    5: ['df = pd.DataFrame({"value": [np.nan, np.nan], "score": [np.nan, 1.0]})\nfill = -1.0',
        'df = pd.DataFrame({"score": [1.0, np.nan, 3.0], "value": [np.nan, 4.0, 2.0]})\nfill = 9.5'],
    6: ['df = pd.DataFrame({"value": [1.0, 2.0], "score": [3.0, 4.0]}, index=["x", "y"])',
        'df = pd.DataFrame({"a": [np.nan, 1.0, 2.0], "b": [1.0, np.nan, 3.0], "c": [5.0, 6.0, 7.0]})'],
    7: ['series = pd.Series([1.0, 2.0])\ntrain_mean = 9.0',
        'series = pd.Series([np.nan, np.nan, 8.0], index=[3, 1, 2])\ntrain_mean = -1.0'],
    8: ['df = pd.DataFrame({"score": [1, 2], "value": [np.nan, np.nan]}, index=["x", "y"])',
        'df = pd.DataFrame({"value": [4.0, 5.0, 6.0]})'],
    9: ['df = pd.DataFrame({"group": ["c", "d"], "value": [1.0, 2.0]})\nfill_values = {"group": "none", "value": -1.0}',
        'df = pd.DataFrame({"value": [np.nan, 3.0], "group": [None, None]}, index=[7, 8])\n'
        'fill_values = {"group": "missing", "value": 5.0}'],
    10: ['df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})',
         'df = pd.DataFrame({"value": [np.nan, np.nan, np.nan, np.nan, 2.0]})'],
    11: ['df = pd.DataFrame({"value": [np.nan, np.nan], "score": [np.nan, np.nan]}, index=["x", "y"])',
         'df = pd.DataFrame({"a": [1.0, np.nan, np.nan], "b": [np.nan, 2.0, np.nan], "c": [np.nan, np.nan, np.nan]})'],
    12: ['df = pd.DataFrame({"a": [1.0, np.nan], "b": [2.0, np.nan], "c": [np.nan, 3.0]})\nmin_valid = 1',
         'df = pd.DataFrame({"a": [1.0, np.nan, 2.0], "b": [np.nan, np.nan, 3.0], "c": [4.0, 5.0, 6.0]})\nmin_valid = 3'],
    13: ['series = pd.Series([2.0, np.nan, np.nan], index=["a", "b", "c"])',
         'series = pd.Series([np.nan, np.nan, 3.0, np.nan, 1.0])'],
    14: ['series = pd.Series([1.0, np.nan, np.nan, 4.0])',
         'series = pd.Series([np.nan, 7.0, np.nan], index=[2, 0, 1])'],
    15: ['train = pd.DataFrame({"x": [2.0, 4.0], "y": [1.0, 1.0]})\ntest = pd.DataFrame({"x": [np.nan], "y": [8.0]})',
         'train = pd.DataFrame({"x": [5.0, 1.0, 3.0, 100.0], "y": [np.nan, 2.0, 4.0, 6.0]})\n'
         'test = pd.DataFrame({"x": [np.nan, np.nan, 0.0], "y": [np.nan, 1.0, np.nan]}, index=["p", "q", "r"])'],
    16: ['df = pd.DataFrame({"group": ["x", "y", "x"], "value": [np.nan, np.nan, 4.0]}, index=["p", "q", "r"])',
         'df = pd.DataFrame({"group": ["b", "a", "b", "a"], "value": [2.0, 6.0, np.nan, np.nan]})'],
    17: ['df = pd.DataFrame({"score": [5, 6], "value": [1.0, np.nan]}, index=["x", "y"])\nfill = 0.0',
         'df = pd.DataFrame({"value": [3.0, 4.0], "score": [1, 1]})\nfill = 9.0'],
    18: ['df = pd.DataFrame({"count": [np.nan, np.nan]})',
         'df = pd.DataFrame({"count": [10.0, 0.0, np.nan]}, index=[4, 5, 6])'],
}

_PRELUDE = """
import math
def _missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v))
_idx = list(df.index) if "df" in globals() else None
def _col(name):
    return df[name].tolist()
def _take(positions):
    return pd.DataFrame({c: [_col(c)[i] for i in positions] for c in df.columns},
                        index=[_idx[i] for i in positions])
def _rows():
    return [[_col(c)[i] for c in df.columns] for i in range(len(df))]
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = sum(1 for v in _col('value') if _missing(v))",
    2: "expected = pd.Series([sum(1 for v in _col(c) if _missing(v)) for c in df.columns], index=list(df.columns))",
    3: "expected = _take([i for i, v in enumerate(_col('value')) if _missing(v)])",
    4: "expected = _take([i for i, v in enumerate(_col('value')) if not _missing(v)])",
    5: ("expected = pd.DataFrame({c: [fill if c == 'value' and _missing(v) else v for v in _col(c)]"
        " for c in df.columns}, index=_idx)"),
    6: "expected = _take([i for i, row in enumerate(_rows()) if not any(_missing(v) for v in row)])",
    7: ("expected = pd.Series([train_mean if _missing(v) else v for v in series.tolist()],"
        " index=list(series.index))"),
    8: ("expected = pd.DataFrame({**{c: _col(c) for c in df.columns},"
        " 'value_missing': [_missing(v) for v in _col('value')]}, index=_idx)"),
    9: ("expected = pd.DataFrame({c: [fill_values[c] if _missing(v) else v for v in _col(c)]"
        " for c in df.columns}, index=_idx)"),
    10: "expected = sum(1 for v in _col('value') if _missing(v)) / len(df)",
    11: "expected = _take([i for i, row in enumerate(_rows()) if not all(_missing(v) for v in row)])",
    12: "expected = _take([i for i, row in enumerate(_rows()) if sum(not _missing(v) for v in row) >= min_valid])",
    13: ("_out, _last = [], float('nan')\n"
         "for v in series.tolist():\n    _last = _last if _missing(v) else v\n    _out.append(_last)\n"
         "expected = pd.Series(_out, index=list(series.index))"),
    14: ("_vals = series.tolist()\n_out, _last = [], None\n"
         "for v in _vals:\n    _last = _last if _missing(v) else v\n    _out.append(_last)\n"
         "_first = next(v for v in _vals if not _missing(v))\n"
         "expected = pd.Series([_first if v is None else v for v in _out], index=list(series.index))"),
    15: ("def _median(vals):\n    vals = sorted(v for v in vals if not _missing(v))\n    k = len(vals)\n"
         "    return vals[k // 2] if k % 2 else (vals[k // 2 - 1] + vals[k // 2]) / 2\n"
         "expected = pd.DataFrame({c: [_median(train[c].tolist()) if _missing(v) else v for v in test[c].tolist()]"
         " for c in test.columns}, index=list(test.index))"),
    16: ("_groups, _vals = _col('group'), _col('value')\n"
         "def _mean(g):\n    vs = [v for k, v in zip(_groups, _vals) if k == g and not _missing(v)]\n"
         "    return sum(vs) / len(vs) if vs else float('nan')\n"
         "expected = pd.Series([_mean(g) if _missing(v) else v for g, v in zip(_groups, _vals)], index=_idx)"),
    17: ("expected = pd.DataFrame({**{c: ([fill if _missing(v) else v for v in _col(c)] if c == 'value' else _col(c))"
         " for c in df.columns}, 'value_missing': [_missing(v) for v in _col('value')]}, index=_idx)"),
    18: "expected = np.array([0 if _missing(v) else int(v) for v in _col('count')], dtype=np.int64)",
}.items()}

RULES = {
    18: {"dtype": True},
}

WRONG = {
    1: ['result = int(df["value"].count())', "result = int(df.isna().sum().sum())"],
    2: ["result = df.isna().sum(axis=1)"],
    3: ['result = df[df["value"].notna()]'],
    4: ["result = df.dropna()"],
    5: ["result = df.fillna(fill)"],
    6: ['result = df.dropna(subset=["value"])'],
    7: ["result = series.fillna(series.mean())"],
    8: ['result = df.assign(value_missing=df["value"].notna())'],
    9: ["result = df.fillna(0.0)", 'result = df.fillna(fill_values["value"])'],
    10: ['result = int(df["value"].isna().sum())'],
    11: ["result = df.dropna()"],
    12: ["result = df.dropna()", "result = df.dropna(thresh=min_valid + 1)"],
    13: ["result = series.bfill()", "result = series.ffill().fillna(0.0)"],
    14: ["result = series.bfill().ffill()", "result = series.ffill()"],
    15: ["result = test.fillna(test.median())", "result = test.fillna(train.mean())"],
    16: ['result = df["value"].fillna(df["value"].mean())'],
    17: ['out = df.fillna({"value": fill})\nresult = out.assign(value_missing=out["value"].isna())'],
    18: ['result = df["count"].fillna(0).to_numpy()', 'result = df["count"].dropna().astype("int64").to_numpy()'],
}


def compile_missing(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
