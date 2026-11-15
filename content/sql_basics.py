"""SQLite course source. Only authored SQL runs during content compilation."""

from contextlib import closing
from dataclasses import dataclass
import sqlite3


MODULE = dict(id="sql", title="SQL", subtitle="SQLiteで表の抽出・集計・結合を練習します。Pythonの知識は不要です。",
              color="#0891b2", icon="database")


def table(name, label, *columns):
    return dict(name=name, description=label, columns=[
        dict(name=name, type=kind, description=description) for name, kind, description in columns
    ])


SALES = [table("sales", "売上明細", ("id", "INTEGER", "明細ID"), ("product", "TEXT", "商品名"),
               ("category", "TEXT", "分類"), ("amount", "INTEGER", "金額"), ("note", "TEXT", "メモ"))]
JOIN_TABLES = [
    table("customers", "顧客", ("id", "INTEGER", "顧客ID（顧客ごとに固有）"), ("name", "TEXT", "顧客名")),
    table("purchases", "購入履歴", ("id", "INTEGER", "購入ID"),
          ("customer_id", "INTEGER", "購入した顧客のID"), ("item", "TEXT", "商品名")),
]

# Different boundaries, duplicates, and row orders. No variant is a new lesson.
SALES_ROWS = [
    [[1, "茶", "飲料", 100, None], [2, "パン", "食品", 200, ""], [3, "茶", "飲料", 200, "再注文"],
     [4, "水", "飲料", 0, None], [5, "皿", "雑貨", 300, "ギフト"]],
    [[4, "米", "食品", 265, ""], [2, "水", "飲料", 100, None], [7, "皿", "雑貨", 100, "予備"],
     [1, "米", "食品", 99, None], [5, "茶", "飲料", 201, ""], [9, "水", "飲料", 200, "試飲"]],
    [[8, "塩", "食品", 200, None], [4, "茶", "飲料", 200, ""], [2, "杯", "雑貨", 300, None],
     [6, "塩", "食品", 0, "見本"], [1, "茶", "飲料", 100, "追加"]],
    [[14, "米", "食品", 500, ""], [12, "皿", "雑貨", 200, ""], [5, "茶", "飲料", 99, None],
     [9, "皿", "雑貨", 200, None], [3, "米", "食品", 100, "試食"], [11, "杯", "雑貨", 0, None]],
    [[5, "麦", "食品", 100, ""], [2, "皿", "雑貨", 200, None], [3, "茶", "飲料", 400, "試飲"],
     [7, "皿", "雑貨", 100, "予備"], [8, "茶", "飲料", 201, None], [10, "麦", "食品", 0, ""]],
]
JOIN_ROWS = [
    [[[1, "葵"], [2, "蓮"], [3, "凛"]], [[1, 2, "米"], [2, 1, "茶"], [3, 1, "水"], [4, None, "皿"]]],
    [[[4, "空"], [1, "海"], [6, "海"]], [[1, 6, "茶"], [2, 4, "水"], [3, 6, "茶"]]],
    [[[5, "梓"], [3, "悠"], [7, "澪"], [2, "梓"]], [[1, 3, "米"], [2, 3, "米"], [3, 5, "皿"], [4, None, "茶"]]],
    [[[3, "楓"], [2, "涼"], [1, "雪"]], [[2, 1, "皿"], [3, 1, "皿"], [4, None, "塩"], [5, 3, "塩"]]],
    [[[10, "葵"], [5, "葵"], [4, "結"]], [[2, 10, "茶"], [7, 10, "米"], [8, 5, "米"], [9, None, "水"]]],
]


@dataclass(frozen=True)
class Lesson:
    title: str
    task: str
    stage: str
    solution: str
    alternative: str
    wrong: str
    hint: str
    explanation: str
    ordered: bool = False
    column_names: bool = False
    approximate: bool = False
    starter: str = ""


COURSE = [
    ("表を見る", "表から全列や必要な列を取り出す。", "SELECT * FROM sales;", [
        Lesson("表の全列を見る", "`sales` の全行・全列を、表と同じ列順で取り出してください。", "guided",
               "SELECT * FROM sales", "SELECT id, product, category, amount, note FROM sales",
               "SELECT id, product FROM sales", "`SELECT` は取り出す列、`FROM` は元の表を指定します。`*` は全列です。",
               "`SELECT * FROM sales` は、売上明細の全列を表の列順で返します。", starter="SELECT \nFROM sales;"),
        Lesson("商品名だけを取り出す", "`sales` の `product` 列だけを全行分取り出してください。", "partial",
               "SELECT product FROM sales", "SELECT s.product FROM sales AS s", "SELECT DISTINCT product FROM sales",
               "`SELECT` の後に列名を1つ書きます。",
               "列を指定しても、行は引き続き1明細につき1行です。同じ商品が複数回売れた場合も残ります。"),
        Lesson("列を選んで名前を付ける", "`sales` の `amount`、`product` の順に全行を取り出し、結果の列名を `price`、`product` にしてください。", "independent",
               "SELECT amount AS price, product FROM sales", "SELECT amount price, product FROM sales",
               "SELECT amount, product FROM sales", "`SELECT` に希望の順で列を書き、`AS` で結果の列に名前を付けます。",
               "`AS price` は結果にだけ付ける列名です。元の表の `amount` はそのままです。", column_names=True),
    ]),
    ("行を絞る", "条件に合う明細を取り出す。", "WHERE amount >= 200", [
        Lesson("金額の下限を指定する", "`sales` から `amount` が200以上の明細の `id` を取り出してください。", "guided",
               "SELECT id FROM sales WHERE amount >= 200", "SELECT id FROM sales WHERE 200 <= amount",
               "SELECT id FROM sales WHERE amount > 200", "`WHERE` は残す行の条件です。`>=` は200ちょうども含みます。",
               "条件を満たす明細だけが残ります。`>` にすると200ちょうどの明細が落ちます。", starter="SELECT id FROM sales\nWHERE "),
        Lesson("2つの条件を両方満たす", "`sales` から、分類 `category` が `'飲料'` で、金額 `amount` が200以上の明細の `id` を取り出してください。", "partial",
               "SELECT id FROM sales WHERE category = '飲料' AND amount >= 200",
               "SELECT id FROM sales WHERE amount >= 200 AND '飲料' = category",
               "SELECT id FROM sales WHERE category = '飲料' OR amount >= 200",
               "文字列は単引用符で囲み、両方を満たす条件は `AND` でつなぎます。",
               "`AND` なら、飲料でも200未満の行や、200以上でも飲料以外の行は残りません。"),
        Lesson("どちらか一方を満たす", "`sales` から、分類 `category` が `'雑貨'` または金額 `amount` が0の明細の `id` を取り出してください。", "partial",
               "SELECT id FROM sales WHERE category = '雑貨' OR amount = 0",
               "SELECT id FROM sales WHERE amount = 0 OR category = '雑貨'",
               "SELECT id FROM sales WHERE category = '雑貨' AND amount = 0",
               "どちらかが真なら残す条件は `OR` です。",
               "`OR` は少なくとも片方を満たす行を残します。両方を満たしても行は1回だけ返ります。"),
        Lesson("候補の一覧で絞る", "`sales` から、分類 `category` が `'飲料'` または `'食品'` の明細の `id` を取り出してください。", "independent",
               "SELECT id FROM sales WHERE category IN ('飲料', '食品')",
               "SELECT id FROM sales WHERE category = '飲料' OR category = '食品'",
               "SELECT id FROM sales WHERE category IN ('飲料', '雑貨')",
               "`IN` の括弧に候補をカンマで並べると、候補のどれかに一致する行を残せます。",
               "同じ列を複数の値と比べるとき、`IN` を使うと候補が見渡しやすくなります。"),
        Lesson("範囲の両端を含める", "`sales` から金額 `amount` が100〜200（両端を含む）の明細の `id` を取り出してください。", "independent",
               "SELECT id FROM sales WHERE amount BETWEEN 100 AND 200",
               "SELECT id FROM sales WHERE amount >= 100 AND amount <= 200",
               "SELECT id FROM sales WHERE amount > 100 AND amount < 200",
               "`BETWEEN 下限 AND 上限` は両端を含みます。",
               "`BETWEEN` はここでは `amount >= 100 AND amount <= 200` と同じです。"),
    ]),
    ("並べ替え・件数", "結果の並び順と返す件数を決める。", "ORDER BY amount DESC, id ASC", [
        Lesson("IDの小さい順に並べる", "`sales` の `product` を、`id` の昇順（小さい順）で取り出してください。", "guided",
               "SELECT product FROM sales ORDER BY id ASC", "SELECT product FROM sales ORDER BY id",
               "SELECT product FROM sales ORDER BY id DESC", "結果の順序は `ORDER BY` で指定します。`ASC` は昇順です。",
               "SQLiteの既定の並び方向は昇順です。表示する列と並べ替えに使う列は別々に指定できます。", ordered=True),
        Lesson("金額の高い順に並べる", "`sales` の `amount` を、金額の降順（大きい順）で取り出してください。", "partial",
               "SELECT amount FROM sales ORDER BY amount DESC", "SELECT amount FROM sales ORDER BY 1 DESC",
               "SELECT amount FROM sales ORDER BY amount", "`DESC` は降順です。並べる列名の後に置きます。",
               "`ORDER BY amount DESC` は金額の大きな値を先に並べます。同額の行も残ります。", ordered=True),
        Lesson("同額の並びを決める", "`sales` の `id`、`amount` を取り出し、金額は降順、同額なら `id` は昇順にしてください。", "partial",
               "SELECT id, amount FROM sales ORDER BY amount DESC, id ASC",
               "SELECT id, amount FROM sales ORDER BY amount DESC, id",
               "SELECT id, amount FROM sales ORDER BY amount DESC, id DESC",
               "`ORDER BY` に列を2つ並べます。第2列は第1列が同じときに使われます。",
               "並び順を列ごとに指定すると、同じ金額でもどの明細が先か決まります。", ordered=True),
        Lesson("上位2件に絞る", "`sales` の `id`、`amount` を取り出してください。金額の降順、同額なら `id` の昇順で並べ、先頭2件だけを返してください。", "independent",
               "SELECT id, amount FROM sales ORDER BY amount DESC, id LIMIT 2",
               "SELECT id, amount FROM sales ORDER BY amount DESC, id LIMIT 2 OFFSET 0",
               "SELECT id, amount FROM sales ORDER BY amount DESC, id",
               "並べ替えの指定の後に `LIMIT 2` を書きます。",
               "`LIMIT` は並べ替えた結果の先頭から返す行数を制限します。", ordered=True),
    ]),
    ("欠損と重複", "NULLや、同じ値が繰り返し出る列を扱う。", "WHERE note IS NULL", [
        Lesson("NULLの行を探す", "`sales` から、メモ `note` が `NULL`（値が入っていない）の明細の `id` を取り出してください。", "guided",
               "SELECT id FROM sales WHERE note IS NULL", "SELECT id FROM sales WHERE NOT (note IS NOT NULL)",
               "SELECT id FROM sales WHERE note = NULL", "`NULL` の判定には `IS NULL` を使います。",
               "`= NULL` は真になりません。`IS NULL` は値が欠けている行だけを見つけ、空文字は残しません。"),
        Lesson("空文字だけを探す", "`sales` から、メモ `note` が空文字 `''` の明細の `id` を取り出してください。", "partial",
               "SELECT id FROM sales WHERE note = ''", "SELECT id FROM sales WHERE '' = note",
               "SELECT id FROM sales WHERE COALESCE(note, '') = ''", "空文字は長さ0の文字列です。`''` と比較します。",
               "`note = ''` が真なのは空文字だけです。`NULL` の明細は条件を通りません。"),
        Lesson("商品の重複を除く", "`sales` の `product` を、同じ商品名は1行だけになるように取り出してください。", "partial",
               "SELECT DISTINCT product FROM sales", "SELECT product FROM sales GROUP BY product",
               "SELECT product FROM sales", "`SELECT DISTINCT` は選んだ列の値が同じ行を1行にまとめます。",
               "商品の一覧だけが欲しいなら、列を `product` に絞ってから重複を除きます。"),
        Lesson("値があるメモを一覧にする", "`sales` の `note` から `NULL` を除き、異なるメモを1行ずつ取り出してください。空文字も値として含めます。", "independent",
               "SELECT DISTINCT note FROM sales WHERE note IS NOT NULL",
               "SELECT note FROM sales WHERE note IS NOT NULL GROUP BY note", "SELECT DISTINCT note FROM sales",
               "`WHERE ... IS NOT NULL` で欠損を除き、`DISTINCT` を使います。",
               "欠損の除外と重複の除外は別の操作です。空文字はこの条件で残ります。"),
    ]),
    ("集計", "表全体の件数や合計、平均、最小・最大を求める。", "SELECT COUNT(*) FROM sales;", [
        Lesson("全明細の件数を数える", "`sales` の全明細の件数を1行1列で返してください。", "guided",
               "SELECT COUNT(*) FROM sales", "SELECT COUNT(id) FROM sales", "SELECT COUNT(note) FROM sales",
               "`COUNT(*)` は列に `NULL` がある行も含め、すべての行を数えます。",
               "メモが空欄の明細も1件です。`COUNT(*)` は行そのものを数えます。"),
        Lesson("値の入ったメモを数える", "`sales` の `note` が `NULL` ではない明細の件数を1行1列で返してください。空文字も数えます。", "partial",
               "SELECT COUNT(note) FROM sales", "SELECT COUNT(*) FROM sales WHERE note IS NOT NULL",
               "SELECT COUNT(*) FROM sales", "`COUNT(列)` はその列の値が `NULL` の行を数えません。",
               "`COUNT(note)` は空文字も1件と数え、値のない `NULL` だけを除外します。"),
        Lesson("金額を合計する", "`sales` の `amount` の合計を1行1列で返してください。", "partial",
               "SELECT SUM(amount) FROM sales", "SELECT SUM(s.amount) FROM sales AS s", "SELECT COUNT(amount) FROM sales",
               "数値の合計には `SUM(列名)` を使います。",
               "`SUM(amount)` は金額を足し上げて1つの値を返します。"),
        Lesson("平均を求める", "`sales` の `amount` の平均を1行1列で返してください。丸めず、金額0の明細も含めます。", "independent",
               "SELECT AVG(amount) FROM sales", "SELECT 1.0 * SUM(amount) / COUNT(amount) FROM sales",
               "SELECT AVG(amount) FROM sales WHERE amount > 0", "`AVG` は平均です。`WHERE` を付けず全明細を対象にします。",
               "金額0の明細も平均の分母に入ります。SQLiteの `AVG` は小数を含む結果を返せます。", approximate=True),
        Lesson("範囲を最小値と最大値で表す", "`sales` の `amount` の最小値、最大値を、この順の2列・1行で返してください。", "independent",
               "SELECT MIN(amount), MAX(amount) FROM sales", "SELECT MIN(s.amount), MAX(s.amount) FROM sales s",
               "SELECT MAX(amount), MIN(amount) FROM sales", "`MIN` は最小値、`MAX` は最大値です。`SELECT` に求める順に書きます。",
               "1回の集計で、別々の集計関数を結果の列として並べられます。"),
    ]),
    ("グループ別集計", "分類ごとに集計し、集計の前後で条件を使い分ける。", "GROUP BY category HAVING COUNT(*) >= 2", [
        Lesson("分類ごとの件数を数える", "`sales` を `category` ごとにまとめ、分類、明細の件数の順で取り出してください。", "guided",
               "SELECT category, COUNT(*) FROM sales GROUP BY category",
               "SELECT category, COUNT(id) FROM sales GROUP BY category", "SELECT category, COUNT(*) FROM sales",
               "`GROUP BY category` は、分類の値が同じ明細を1組にします。",
               "分類ごとに1行が返り、`COUNT(*)` はその組の明細だけを数えます。"),
        Lesson("対象の明細を絞ってから集計する", "`sales` の金額 `amount` が200以上の明細だけを使い、`category`、分類ごとの合計金額の順で返してください。", "partial",
               "SELECT category, SUM(amount) FROM sales WHERE amount >= 200 GROUP BY category",
               "SELECT category, SUM(amount) FROM (SELECT category, amount FROM sales WHERE amount >= 200) GROUP BY category",
               "SELECT category, SUM(amount) FROM sales GROUP BY category HAVING SUM(amount) >= 200",
               "明細ごとの条件は `WHERE` に置き、残った行を `GROUP BY` でまとめます。",
               "`WHERE amount >= 200` で対象の明細を確定してから、分類ごとに金額を足します。"),
        Lesson("件数の多い分類を残す", "`sales` を `category` ごとに集計し、明細が2件以上ある分類の `category`、明細の件数を返してください。", "partial",
               "SELECT category, COUNT(*) FROM sales GROUP BY category HAVING COUNT(*) >= 2",
               "SELECT category, n FROM (SELECT category, COUNT(*) AS n FROM sales GROUP BY category) WHERE n >= 2",
               "SELECT category, COUNT(*) FROM sales GROUP BY category HAVING COUNT(*) > 2",
               "グループを作った後の条件には `HAVING` を使います。",
               "`HAVING COUNT(*) >= 2` は行ごとの条件ではなく、集計済みの分類ごとの条件です。"),
        Lesson("対象行と集計結果を両方絞る", "`sales` の金額 `amount` が100以上の明細だけを使います。その明細が2件以上ある分類の `category`、件数の順で返してください。", "independent",
               "SELECT category, COUNT(*) FROM sales WHERE amount >= 100 GROUP BY category HAVING COUNT(*) >= 2",
               "SELECT category, n FROM (SELECT category, COUNT(*) AS n FROM sales WHERE amount >= 100 GROUP BY category) WHERE n >= 2",
               "SELECT category, COUNT(*) FROM sales GROUP BY category HAVING COUNT(*) >= 2",
               "各明細の金額は `WHERE`、分類ごとの件数は `HAVING` で絞ります。",
               "100未満の明細を除いてから数えると、分類そのものが結果に残らなくなる場合があります。"),
    ]),
    ("テーブルの結合", "IDを使って顧客と購入履歴を結び付ける。", "JOIN purchases ON customers.id = purchases.customer_id", [
        Lesson("購入に対応する顧客名を出す", "`purchases.customer_id` に対応する `customers.id` がある購入の `customers.name`、`purchases.item` を返してください。", "guided",
               "SELECT customers.name, purchases.item FROM purchases INNER JOIN customers ON purchases.customer_id = customers.id",
               "SELECT c.name, p.item FROM customers AS c JOIN purchases AS p ON p.customer_id = c.id",
               "SELECT customers.name, purchases.item FROM purchases JOIN customers ON purchases.id = customers.id",
               "IDは行を識別する値です。`JOIN ... ON` で、購入の顧客IDと顧客表のIDを対応させます。",
               "`INNER JOIN` は結合条件に合う組だけを返します。購入IDではなく、購入者のIDを使います。"),
        Lesson("購入ごとの対応を確認する", "`customers` と `purchases` を顧客IDで結び付け、購入がある顧客の `customers.id`、`purchases.id` を購入1件につき1行返してください。", "partial",
               "SELECT c.id, p.id FROM customers c JOIN purchases p ON c.id = p.customer_id",
               "SELECT p.customer_id, p.id FROM purchases p WHERE p.customer_id IN (SELECT id FROM customers)",
               "SELECT c.id, p.id FROM customers c JOIN purchases p ON c.id = p.id",
               "両方の表に `id` があるので、どちらの列かを `表名.id` で示します。",
               "同じ顧客IDの購入が2件なら2行返ります。列名が同じでも、2つの `id` は別の値です。"),
        Lesson("購入がない顧客も含める", "全 `customers` の `name` と、顧客IDが一致する購入の `purchases.item` を返してください。購入がない顧客も `item` を `NULL` として1行残します。", "partial",
               "SELECT c.name, p.item FROM customers c LEFT JOIN purchases p ON c.id = p.customer_id",
               "SELECT c.name, p.item FROM customers c LEFT OUTER JOIN purchases p ON p.customer_id = c.id",
               "SELECT c.name, p.item FROM customers c JOIN purchases p ON c.id = p.customer_id",
               "`LEFT JOIN` は左側の表の行を残します。左側に `customers` を置いてください。",
               "購入がない顧客の行は残り、右側の `item` に `NULL` が入ります。"),
        Lesson("購入がない顧客だけを探す", "`customers` のうち、顧客IDが一致する `purchases` が1件もない顧客の `customers.id` を返してください。", "independent",
               "SELECT c.id FROM customers c LEFT JOIN purchases p ON c.id = p.customer_id WHERE p.id IS NULL",
               "SELECT c.id FROM customers c WHERE NOT EXISTS (SELECT 1 FROM purchases p WHERE p.customer_id = c.id)",
               "SELECT id FROM customers WHERE id NOT IN (SELECT customer_id FROM purchases)",
               "`LEFT JOIN` すると、購入がない顧客の右側の購入IDは `NULL` になります。",
               "`p.id IS NULL` で対応する購入が無い行を残せます。顧客IDが `NULL` の購入はどの顧客にも一致しません。"),
    ]),
]


def evaluate(tables, rows, code):
    with closing(sqlite3.connect(":memory:")) as db:
        for schema, values in zip(tables, rows, strict=True):
            columns = ", ".join(f"{c['name']} {c['type']}" for c in schema["columns"])
            db.execute(f"CREATE TABLE {schema['name']} ({columns})")
            placeholders = ",".join("?" for _ in schema["columns"])
            db.executemany(f"INSERT INTO {schema['name']} VALUES ({placeholders})", values)
        result = db.execute(code)
        return dict(columns=[c[0] for c in result.description], rows=[list(row) for row in result])


GENERATOR = "sqlite-fixtures-v1"
STAGES = ("guided", "partial", "independent")


def compile_sql(seed, start_order):
    concepts, problems = [], []
    for number, (title, description, example, lessons) in enumerate(COURSE, 1):
        cid = f"SQL{number:02}"
        prerequisites = [f"SQL{number - 1:02}"] if number > 1 else []
        concepts.append(dict(id=cid, module_id=MODULE["id"], title=title, description=description, example=example,
                             prerequisites=prerequisites, order=start_order + number - 1,
                             ordered_practice=True, problem_count=len(lessons), mastery_available=False))
        tables, fixtures = (JOIN_TABLES, JOIN_ROWS) if number == 7 else (SALES, [[rows] for rows in SALES_ROWS])
        for index, lesson in enumerate(lessons, 1):
            pid = f"{cid}-{index:02}"
            indices = (0, 1, 3) if seed == 42 else (1, 2, 4)
            cases = [dict(rows=fixtures[i], expected=evaluate(tables, fixtures[i], lesson.solution)) for i in indices]
            problems.append(dict(
                id=pid, family_id=pid, version_id=f"{pid}@1", content_version=1, concept_id=cid,
                module_id=MODULE["id"], stage=lesson.stage, type="implementation",
                difficulty=STAGES.index(lesson.stage) + 1, title=lesson.title, description=lesson.task,
                learning_goal=description, input_conditions="", output_conditions="", starter_code=lesson.starter,
                example="", editable_regions=[], hints=[lesson.hint], solution=lesson.solution,
                explanation=lesson.explanation, common_mistakes=[], public_tests=[], hidden_tests=cases[2:],
                required_ast="", check_dtype=False, runtime="browser", packages=[], prerequisites=prerequisites,
                estimated_minutes=2, variant_seed=seed, variant_generator=GENERATOR, tolerance=1e-8,
                sql=dict(tables=tables, cases=cases[:2], ordered=lesson.ordered, column_names=lesson.column_names,
                         approximate=lesson.approximate),
            ))
    return concepts, problems
