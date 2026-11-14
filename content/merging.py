"""PD04: merge, join and concat, with attention to rows, columns and index."""

from content.ordered import compile_ordered, load_lessons

CONCEPT_ID = "PD04"
LESSONS = load_lessons(__file__)


def df(var, index=None, **columns):
    suffix = "" if index is None else f", index={index!r}"
    return f"{var} = pd.DataFrame({columns!r}{suffix})"


def pair(left, right):
    return df("left", **left) + "\n" + df("right", **right)


ALTERNATIVES = {
    1: [pair(dict(id=[2, 2, 1], name=["P", "Q", "R"]), dict(id=[1, 2], price=[5, 6])),
        pair(dict(id=[7], name=["Z"]), dict(id=[1], price=[3]))],
    2: [pair(dict(id=[2, 2, 1], name=["P", "Q", "R"]), dict(id=[1, 2], price=[5, 6])),
        pair(dict(id=[7, 8], name=["Y", "Z"]), dict(id=[1], price=[3]))],
    3: [df("a", [5, 6], id=[1, 2], score=[1, 2]) + "\n" + df("b", [5], id=[9], score=[0]),
        df("a", id=[1], score=[3]) + "\n" + df("b", ["x", "y"], id=[2, 3], score=[4, 5])],
    4: [df("a", [5, 6], id=[1, 2], score=[1, 2]) + "\n" + df("b", [5], id=[9], score=[0]),
        df("a", id=[1], score=[3]) + "\n" + df("b", [10, 20], id=[2, 3], score=[4, 5])],
    5: [pair(dict(id=[1, 2], name=["A", "B"]), dict(id=[1, 2], price=[5, 6])),
        pair(dict(id=[5, 4], name=["E", "D"]), dict(id=[6, 3, 4], price=[60, 30, 40]))],
    6: [df("left", user_id=[5, 4], name=["E", "D"]) + "\n" + df("right", id=[4, 5], city=["Oita", "Saga"]),
        df("left", user_id=[1], name=["A"]) + "\n" + df("right", id=[9], city=["Mito"])],
    7: [df("a", [10, 20], value=[0.5, 1.5]) + "\n" + df("b", [20, 10], score=[1, 2]),
        df("a", ["p", "q"], value=[1.0, 2.0]) + "\n" + df("b", ["r"], score=[3])],
    8: [df("a", ["x", "y"], value=[1.0, 2.0]) + "\n" + df("b", ["y", "z"], score=[5, 6]),
        df("a", [0, 1], value=[1.0, 2.0]) + "\n" + df("b", [0, 1], score=[3, 4])],
    9: [pair(dict(id=[3, 4, 5], score=[1, 2, 3]), dict(id=[5, 3], score=[30, 10])),
        pair(dict(id=[1], score=[0]), dict(id=[1], score=[9]))],
    10: [df("sales", store=["B", "A"], day=[2, 2], amount=[10, 20]) + "\n"
         + df("targets", store=["A", "B"], day=[2, 2], target=[25, 15]),
         df("sales", store=["A"], day=[3], amount=[1]) + "\n" + df("targets", store=["A"], day=[1], target=[5])],
    11: [pair(dict(id=[5, 6], name=["E", "F"]), dict(id=[5, 6], price=[1, 2])),
         df("left", [10, 20, 30], id=[1, 2, 3], name=["A", "B", "C"]) + "\n" + df("right", id=[2], price=[9])],
    12: [df("a", id=[1], x=[2.0], z=["p"]) + "\n" + df("b", id=[2, 3], z=["q", "r"]),
         df("a", [4, 5], id=[1, 2], x=[1.0, 2.0]) + "\n" + df("b", [4], y=[3.0], id=[3])],
    13: [pair(dict(id=[2, 2], qty=[1, 1]), dict(id=[2, 1], price=[10, 20])),
         pair(dict(id=[3, 1, 3], qty=[1, 2, 3]), dict(id=[1], price=[7]))],
    14: [pair(dict(id=[4, 5], name=["D", "E"]), dict(id=[6], price=[1.0])),
         pair(dict(id=[1, 2], name=["A", "B"]), dict(id=[2, 1], price=[2.5, 1.5]))],
    15: [df("orders", product=["cup"], qty=[4]) + "\n" + df("prices", product=["cup", "pen"], price=[400, 120]),
         df("orders", product=["ink", "pen", "ink"], qty=[1, 2, 5]) + "\n"
         + df("prices", product=["pen", "ink"], price=[100, 30])],
    16: [df("customers", id=[3, 1], name=["C", "A"]) + "\n" + df("payments", id=[3, 3, 3], amount=[1.0, 2.0, 3.0]),
         df("customers", id=[5], name=["E"]) + "\n" + df("payments", id=[6], amount=[9.0])],
    17: [df("left", [10, 20], id=[1, 1], name=["A", "B"]) + "\n" + df("right", id=[1], price=[5]),
         df("left", ["x", "y", "z"], id=[3, 9, 2], name=["C", "I", "B"]) + "\n" + df("right", id=[2, 3], price=[2, 3])],
    18: [df("a", [1, 2, 3], value=[1.0, 2.0, 3.0]) + "\n" + df("b", [3, 1, 2], score=[30, 10, 20]),
         df("a", ["p", "q"], value=[1.0, 2.0]) + "\n" + df("b", ["r"], score=[3])],
}

# Independent row-by-row join semantics (pandas: left/inner keep left order,
# outer sorts keys; unmatched columns are NaN).
_PRELUDE = """
NAN = float("nan")
def _records(frame):
    return [dict(zip(frame.columns, row)) for row in frame.to_numpy(dtype=object).tolist()]
def _merge(left, right, on, how, suffixes=("_x", "_y")):
    on = [on] if isinstance(on, str) else list(on)
    lcols = list(left.columns)
    rcols = [c for c in right.columns if c not in on]
    overlap = set(lcols) & set(rcols)
    columns = [c + suffixes[0] if c in overlap else c for c in lcols]
    columns += [c + suffixes[1] if c in overlap else c for c in rcols]
    key = lambda r: tuple(r[k] for k in on)
    L, R = _records(left), _records(right)
    rows, used = [], set()
    for l in L:
        matches = [j for j, r in enumerate(R) if key(r) == key(l)]
        for j in matches:
            used.add(j)
            rows.append([l[c] for c in lcols] + [R[j][c] for c in rcols])
        if not matches and how in ("left", "outer"):
            rows.append([l[c] for c in lcols] + [NAN] * len(rcols))
    if how == "outer":
        for j, r in enumerate(R):
            if j not in used:
                rows.append([r[c] if c in on else NAN for c in lcols] + [r[c] for c in rcols])
        rows.sort(key=lambda row: tuple(row[lcols.index(k)] for k in on))
    return pd.DataFrame(rows, columns=columns)
def _stack(frames, ignore_index):
    columns = []
    for f in frames:
        columns += [c for c in f.columns if c not in columns]
    rows = [[r.get(c, NAN) for c in columns] for f in frames for r in _records(f)]
    index = None if ignore_index else [i for f in frames for i in f.index]
    return pd.DataFrame(rows, columns=columns, index=index)
def _side(a, b, labels):
    ra = dict(zip(a.index, _records(a)))
    rb = dict(zip(b.index, _records(b)))
    return pd.DataFrame([[ra.get(i, {}).get(c, NAN) for c in a.columns] + [rb.get(i, {}).get(c, NAN) for c in b.columns]
                         for i in labels], columns=list(a.columns) + list(b.columns), index=labels)
"""

ORACLES = {n: _PRELUDE + body for n, body in {
    1: "expected = _merge(left, right, 'id', 'left')",
    2: "expected = _merge(left, right, 'id', 'inner')",
    3: "expected = _stack([a, b], True)",
    4: "expected = _stack([a, b], False)",
    5: "expected = _merge(left, right, 'id', 'outer')",
    6: ("_rows = []\nfor l in _records(left):\n"
        "    _ms = [r for r in _records(right) if r['id'] == l['user_id']]\n"
        "    _rows += [[l[c] for c in left.columns] + [r[c] for c in right.columns] for r in _ms]"
        " or [[l[c] for c in left.columns] + [NAN] * len(right.columns)]\n"
        "expected = pd.DataFrame(_rows, columns=list(left.columns) + list(right.columns))"),
    7: "expected = _side(a, b, list(a.index))",
    8: ("_labels = list(a.index) + [i for i in b.index if i not in list(a.index)]\n"
        "expected = _side(a, b, _labels)"),
    9: "expected = _merge(left, right, 'id', 'inner', ('_left', '_right'))",
    10: "expected = _merge(sales, targets, ['store', 'day'], 'left')",
    11: ("_ids = set(right['id'].tolist())\n_keep = [i for i, v in enumerate(left['id'].tolist()) if v not in _ids]\n"
         "expected = pd.DataFrame([[left[c].tolist()[i] for c in left.columns] for i in _keep],"
         " columns=list(left.columns), index=[list(left.index)[i] for i in _keep])"),
    12: "expected = _stack([a, b], True)",
    13: "expected = _merge(left, right, 'id', 'left')",
    14: ("_m = _merge(left, right, 'id', 'left')\n"
         "expected = _m.assign(price=[0.0 if p != p else p for p in _m['price'].tolist()])"),
    15: ("_m = _merge(orders, prices, 'product', 'left')\n"
         "expected = pd.DataFrame([r + [r[1] * r[2]] for r in _m.to_numpy(dtype=object).tolist()],"
         " columns=list(_m.columns) + ['amount'])"),
    16: ("_tot = {}\nfor i, v in zip(payments['id'].tolist(), payments['amount'].tolist()):\n"
         "    _tot[i] = _tot.get(i, 0.0) + v\n"
         "expected = customers.assign(amount=[_tot.get(i, 0.0) for i in customers['id'].tolist()])"),
    17: ("_m = _merge(left, right, 'id', 'left')\n"
         "expected = pd.DataFrame(_m.to_numpy(dtype=object).tolist(), columns=list(_m.columns), index=list(left.index))"),
    18: "expected = _side(a, b, [i for i in a.index if i in list(b.index)])",
}.items()}

RULES = {
    8: {"required": "call:concat"},
    13: {"required": 'call-keywords:{"name": "merge", "keywords": {"validate": "many_to_one"}}'},
    18: {"required": "call:concat"},
}

WRONG = {
    1: ['result = left.merge(right, on="id", how="inner")'],
    2: ['result = left.merge(right, on="id", how="left")'],
    3: ["result = pd.concat([a, b])"],
    4: ["result = pd.concat([a, b], ignore_index=True)"],
    5: ['result = left.merge(right, on="id", how="left")', 'result = pd.concat([left, right], ignore_index=True)'],
    6: ['result = left.merge(right, left_on="user_id", right_on="id", how="inner")'],
    7: ['result = a.join(b, how="inner")', 'result = b.join(a, how="right")'],
    8: ['result = pd.concat([a.reset_index(drop=True), b.reset_index(drop=True)], axis=1)',
         'result = pd.concat([a, b], axis=1, join="inner")'],
    9: ['result = left.merge(right, on="id", how="inner")'],
    10: ['result = sales.merge(targets, on="store", how="left")'],
    11: ['result = left[left["id"].isin(right["id"])]', 'result = left[~left["id"].isin(right["id"])].reset_index(drop=True)'],
    12: ['result = pd.concat([a, b], ignore_index=True, join="inner")'],
    13: ['result = left.merge(right, on="id", how="left")'],
    14: ['result = left.merge(right, on="id", how="inner")', 'result = left.merge(right, on="id", how="left")'],
    15: ['merged = orders.merge(prices, on="product", how="inner", sort=True)\nresult = merged.assign(amount=merged["qty"] * merged["price"])'],
    16: ['result = customers.merge(payments, on="id", how="left").fillna({"amount": 0})'],
    17: ['result = left.merge(right, on="id", how="left")'],
    18: ['result = pd.concat([a, b], axis=1)', 'result = b.join(a, how="inner")'],
}


def compile_merging(concept, seed):
    return compile_ordered(concept, seed, CONCEPT_ID, LESSONS, ALTERNATIVES, ORACLES, RULES)
