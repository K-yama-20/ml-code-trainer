"""PD01: label and position based selection with loc, iloc and boolean masks."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PD01"
LESSONS = load_lessons(__file__)


def frame(index, **columns):
    return f"df = pd.DataFrame({columns!r}, index={index!r})"


A = frame(["r1", "r2", "r3"], name=["Eri", "Fumi", "Gen"], group=["b", "a", "a"], score=[5, 8, 2])
B = frame([10, 3, 7, 1, 4], name=["Hana", "Ian", "Jun", "Ken", "Lia"],
          group=["a", "a", "b", "b", "a"], score=[4, 9, 9, 1, 6])
SWAPPED = frame(["x", "y", "z"], score=[1, 2, 3], group=["b", "a", "b"], name=["P", "Q", "R"])

ALTERNATIVES = {
    1: [A, B],
    2: [SWAPPED, B],
    3: [A + '\nlabel = "r1"', B + "\nlabel = 1"],
    4: [frame([5], name=["Solo"], score=[1]), B],
    5: [A + "\nthreshold = 8", B + "\nthreshold = 10"],
    6: [SWAPPED, B],
    7: [A + '\nstart = "r1"\nstop = "r2"', B + "\nstart = 3\nstop = 1"],
    8: [A + "\nmin_score = 2", B + "\nmin_score = 7"],
    9: [A + "\nlow = 5\nhigh = 5", B + "\nlow = 1\nhigh = 9"],
    10: [A + '\nnames = ["Gen", "Eri"]', B + '\nnames = ["Nobody"]'],
    11: [A + "\nthreshold = 4", B + "\nthreshold = 9"],
    12: [A, B],
    13: [A + "\nthreshold = 5", B + "\nthreshold = 100"],
    14: [A + "\nthreshold = 3", B + "\nthreshold = 9"],
    15: [A + "\nlow = 2\nhigh = 5", B + "\nlow = 6\nhigh = 8"],
    16: [A + '\nlabels = ["r2"]', B + "\nlabels = [4, 10, 7]"],
    17: [A + "\nthreshold = 9", B + "\nthreshold = 6"],
    18: [A, B],
}

# Plain-Python oracle: positions are computed from lists, then the expected
# table is rebuilt from scratch instead of reusing the learner's operation.
_PRELUDE = """
_idx = list(df.index)
_rows = list(range(len(df)))
_score = df["score"].tolist()
def _take(positions, columns=None):
    columns = list(df.columns) if columns is None else columns
    return pd.DataFrame({c: [df[c].tolist()[i] for i in positions] for c in columns},
                        index=[_idx[i] for i in positions])
def _series(column, positions):
    return pd.Series([df[column].tolist()[i] for i in positions], index=[_idx[i] for i in positions])
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _series('score', _rows)",
    2: "expected = _take(_rows, ['name', 'score'])",
    3: "expected = _score[_idx.index(label)]",
    4: "expected = _take(_rows[:2])",
    5: "expected = _take([i for i in _rows if _score[i] >= threshold])",
    6: "expected = _take([1, 2], [list(df.columns)[0], list(df.columns)[2]])",
    7: "expected = _series('score', list(range(_idx.index(start), _idx.index(stop) + 1)))",
    8: "expected = _take([i for i in _rows if df['group'].tolist()[i] == 'a' and _score[i] >= min_score])",
    9: "expected = _take([i for i in _rows if _score[i] < low or _score[i] > high])",
    10: "expected = _take([i for i in _rows if df['name'].tolist()[i] in names])",
    11: "expected = _take([i for i in _rows if _score[i] > threshold], ['name', 'score'])",
    12: "expected = _score[-1]",
    13: ("expected = pd.DataFrame({c: ([0 if s < threshold else s for s in _score] if c == 'score'"
         " else df[c].tolist()) for c in df.columns}, index=_idx)"),
    14: ("_keep = [i for i in _rows if _score[i] >= threshold]\n"
         "expected = pd.DataFrame({c: [df[c].tolist()[i] for i in _keep] for c in df.columns})"),
    15: "expected = _series('name', [i for i in _rows if low <= _score[i] <= high])",
    16: "expected = _take([_idx.index(label) for label in labels], ['name', 'score'])",
    17: "expected = [_idx[i] for i in _rows if _score[i] >= threshold]",
    18: "expected = df['name'].tolist()[_score.index(max(_score))]",
}.items()}

RULES = {
    3: {"required": "attr:loc"},
    4: {"required": "attr:iloc"},
    6: {"required": "attr:iloc"},
    7: {"required": "attr:loc"},
    10: {"required": "call:isin"},
    11: {"required": "attr:loc"},
    13: {"protect_inputs": True},
    15: {"required": "call:between"},
}

WRONG = {
    1: ['result = df[["score"]]'],
    2: ["result = df.iloc[:, [0, 2]]"],
    3: ['result = df["score"].iloc[2]'],
    4: ["result = df.iloc[1:3]"],
    5: ['result = df[df["score"] > threshold]'],
    6: ["result = df.iloc[1:3, [0, 1]]", 'result = df.iloc[[1, 2]][["name", "score"]]'],
    7: ['result = df["score"].iloc[df.index.get_loc(start):df.index.get_loc(stop)]'],
    8: ['result = df[(df["group"] == "a") | (df["score"] >= min_score)]'],
    9: ['result = df[(df["score"] <= low) | (df["score"] >= high)]'],
    10: ['result = df[df["name"] == names[0]]'],
    11: ['result = df.loc[df["score"] > threshold, "score"]',
         'result = df.loc[df["score"] > threshold, ["score", "name"]]'],
    12: ['result = df["score"].iloc[0]'],
    13: ['df.loc[df["score"] < threshold, "score"] = 0\nresult = df',
         'out = df.copy()\nout.loc[out["score"] <= threshold, "score"] = 0\nresult = out'],
    14: ['result = df[df["score"] >= threshold].reset_index()'],
    15: ['result = df.loc[df["score"].between(low, high, inclusive="neither"), "name"]'],
    16: ['result = df[df.index.isin(labels)][["name", "score"]]'],
    17: ['result = df[df["score"] >= threshold]["name"].tolist()'],
    18: ['result = df.sort_values("score").iloc[-1]["name"]'],
}


def compile_selection(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
