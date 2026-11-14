"""PD03: groupby aggregation, transform and group-level filtering."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PD03"
LESSONS = load_lessons(__file__)


def frame(index=None, **columns):
    suffix = "" if index is None else f", index={index!r}"
    return f"df = pd.DataFrame({columns!r}{suffix})"


ALTERNATIVES = {
    1: [frame(group=["x", "y", "x"], value=[2.0, 6.0, 4.0]),
        frame(group=["c", "c", "a", "b"], value=[1.0, None, 7.0, 2.5])],
    2: [frame(group=["x", "x", "x"], value=[1.0, 2.0, 3.0]),
        frame(group=["c", "a", "c", "b"], value=[None, None, 1.0, None])],
    3: [frame(group=["x", "y", "x"], value=[None, None, 3.0]),
        frame(group=["c", "a", "c", "b"], value=[1.0, 2.0, 3.0, 4.0])],
    4: [frame(group=["x", "y", "x"], score=[10, -1, 5]),
        frame(group=["c", "a", "c", "b", "a"], score=[1, 2, 3, 4, 5])],
    5: [frame(group=["x", "y", "x"], score=[-3, -1, -5]),
        frame(group=["c", "a", "c", "b"], score=[0, 8, 8, 1])],
    6: [frame(group=["a", "a", "b"], kind=["y", "x", "y"], score=[1, 2, 3]),
        frame(group=["c", "b", "c", "b"], kind=["x", "x", "x", "y"], score=[5, 1, 2, 3])],
    7: [frame(group=["x", "x"], value=[3.0, -1.0]),
        frame(group=["c", "a", "c", "b"], value=[2.0, 2.0, 9.0, -4.0])],
    8: [frame(group=["x", "y", "x"], score=[10, -1, 5]),
        frame(group=["c", "a", "c", "b", "a"], score=[1, 2, 3, 4, 5])],
    9: [frame(group=["x", "y", "x"], score=[1, 2, 3], value=[0.5, 1.5, 2.5]),
        frame(group=["c", "a", "c"], value=[4.0, 2.0, 6.0], score=[3, 8, 7])],
    10: [frame(group=["z", "y", "x", "z"], score=[1, 2, 3, 4]),
         frame(group=["a", "a", "b"], score=[5, 6, 7])],
    11: [frame(group=["x", "y", "x"], score=[1, 2, 3], value=[0.5, 1.5, 2.5]),
         frame(group=["c", "a", "c"], value=[4.0, 2.0, 6.0], score=[3, 8, 7])],
    12: [frame(group=["x", "y", "z", "x"], score=[1, 1, 1, 1]),
         frame(group=["b", "a", "b"], score=[3, 5, 2])],
    13: [frame(["p", "q", "r"], group=["x", "x", "y"], score=[1, 5, 3]),
         frame(group=["c", "a", "c", "b"], score=[10, 2, 20, 7])],
    14: [frame(group=["x", "y", "x"], score=[1.0, 4.0, 3.0]),
         frame(group=["c", "a", "c", "c"], score=[6.0, None, None, 2.0])],
    15: [frame(["p", "q", "r"], group=["x", "y", "x"], score=[5, 1, -2]),
         frame(group=["a", "a", "a", "b"], score=[1, 2, 3, 4])],
    16: [frame(["p", "q", "r"], group=["x", "y", "x"], score=[5, 1, 6]) + "\nthreshold = 5.5",
         frame(group=["a", "b", "a"], score=[1, 2, 3]) + "\nthreshold = 10"],
    17: [frame([10, 20, 30], group=["y", "x", "y"], name=["A", "B", "C"], score=[1, 5, 3]),
         frame(group=["c", "a", "c", "b"], name=["D", "E", "F", "G"], score=[7, 2, 7, 0])],
    18: [frame(["p", "q", "r"], group=["x", "y", "x"], score=[1, 5, 3]),
         frame(group=["c", "a", "c", "b"], score=[10, 2, 30, 7])],
}

_PRELUDE = """
import math
def _missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v))
_g = df["group"].tolist()
_idx = list(df.index)
def _keys(sort=True):
    keys = []
    for k in _g:
        if k not in keys:
            keys.append(k)
    return sorted(keys) if sort else keys
def _vals(column, key):
    return [v for g, v in zip(_g, df[column].tolist()) if g == key]
def _valid(values):
    return [v for v in values if not _missing(v)]
def _mean(values):
    values = _valid(values)
    return sum(values) / len(values) if values else float("nan")
def _per_key(f, column, sort=True):
    keys = _keys(sort)
    return pd.Series([f(_vals(column, k)) for k in keys], index=keys)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _per_key(_mean, 'value')",
    2: "expected = _per_key(len, 'value')",
    3: "expected = _per_key(lambda vs: len(_valid(vs)), 'value')",
    4: "expected = _per_key(sum, 'score')",
    5: "expected = _per_key(max, 'score')",
    6: ("_pairs = sorted(set(zip(_g, df['kind'].tolist())))\n"
        "expected = pd.Series([sum(s for g, k, s in zip(_g, df['kind'].tolist(), df['score'].tolist())"
        " if (g, k) == p) for p in _pairs], index=pd.MultiIndex.from_tuples(_pairs))"),
    7: ("expected = pd.DataFrame({'min': [min(_vals('value', k)) for k in _keys()],"
        " 'max': [max(_vals('value', k)) for k in _keys()]}, index=_keys())"),
    8: "expected = pd.DataFrame({'group': _keys(), 'score': [sum(_vals('score', k)) for k in _keys()]})",
    9: ("expected = pd.DataFrame({c: [_mean(_vals(c, k)) for k in _keys()] for c in ['score', 'value']},"
        " index=_keys())"),
    10: "expected = _per_key(sum, 'score', sort=False)",
    11: ("expected = pd.DataFrame({'value': [sum(_vals('value', k)) for k in _keys()],"
         " 'score': [max(_vals('score', k)) for k in _keys()]}, index=_keys())"),
    12: "_total = sum(df['score'].tolist())\nexpected = _per_key(lambda vs: sum(vs) / _total, 'score')",
    13: "expected = pd.Series([s - _mean(_vals('score', g)) for g, s in zip(_g, df['score'].tolist())], index=_idx)",
    14: ("expected = pd.DataFrame({'mean_score': [_mean(_vals('score', k)) for k in _keys()],"
         " 'n': [len(_vals('score', k)) for k in _keys()]}, index=_keys())"),
    15: ("_run, _out = {}, []\nfor g, s in zip(_g, df['score'].tolist()):\n"
         "    _run[g] = _run.get(g, 0) + s\n    _out.append(_run[g])\n"
         "expected = pd.Series(_out, index=_idx)"),
    16: ("_keep = [i for i, g in enumerate(_g) if _mean(_vals('score', g)) >= threshold]\n"
         "expected = pd.DataFrame({c: [df[c].tolist()[i] for i in _keep] for c in df.columns},"
         " index=[_idx[i] for i in _keep])"),
    17: ("_scores = df['score'].tolist()\n"
         "_best = [max((i for i, g in enumerate(_g) if g == k), key=lambda i: (_scores[i], -i)) for k in _keys()]\n"
         "expected = pd.DataFrame({c: [df[c].tolist()[i] for i in _best] for c in df.columns},"
         " index=[_idx[i] for i in _best])"),
    18: "expected = pd.Series([s / sum(_vals('score', g)) for g, s in zip(_g, df['score'].tolist())], index=_idx)",
}.items()}

RULES = {}

WRONG = {
    1: ['result = df.groupby("group", sort=False)["value"].mean()', 'result = df.groupby("group")["value"].sum()'],
    2: ['result = df.groupby("group")["value"].count()'],
    3: ['result = df.groupby("group").size()'],
    4: ['result = df.groupby("group")["score"].mean()'],
    5: ['result = df.groupby("group")["score"].min()'],
    6: ['result = df.groupby("group")["score"].sum()', 'result = df.groupby(["kind", "group"])["score"].sum()'],
    7: ['result = df.groupby("group")["value"].agg(["max", "min"])'],
    8: ['result = df.groupby("group")["score"].sum()', 'result = df.groupby("group", as_index=False, sort=False)["score"].sum()'],
    9: ['result = df.groupby("group")[["value", "score"]].mean()'],
    10: ['result = df.groupby("group")["score"].sum()'],
    11: ['result = df.groupby("group").agg({"value": "max", "score": "sum"})'],
    12: ['result = df.groupby("group")["score"].sum() / len(df)', 'result = df.groupby("group")["score"].mean()'],
    13: ['result = df["score"] - df["score"].mean()'],
    14: ['result = df.groupby("group").agg(mean_score=("score", "mean"), n=("score", "count"))'],
    15: ['result = df["score"].cumsum()'],
    16: ['result = df[df["score"] >= threshold]'],
    17: ['result = df.sort_values("score").groupby("group").tail(1).sort_values("group")'],
    18: ['result = df["score"] / df["score"].sum()'],
}


def compile_groupby(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
