"""Authored Phase 1 lessons. Only these 15 families receive a new content version."""

LESSONS = {
    "PY01-01": dict(
        title="正の数を選んで二乗する",
        description="valuesから0より大きい数だけを選び、それぞれを二乗したリストを返してください。元の並び順は変えません。",
        input="values：数値のリスト。空のリストが渡されることもあります。",
        output="正の数を二乗したリスト。0と負の数は含めません。",
        edit="___を1か所埋めます。関数名と引数は変えず、returnで結果を返してください。",
        sample="入力 [-2, 0, 3] → 選ぶと [3] → 二乗すると [9]",
        hints=[
            "最初に、二乗する数と除く数を分けましょう。0は正の数に入りません。",
            "valuesが[-2, 0, 3]なら、条件を満たすのは3だけです。ifの右側は二乗する前のvを判定します。",
            "正の数の条件はv > 0です。空欄は比較の基準となる値です。",
        ],
        explanation="条件で元の値を選び、その後でv * vを計算します。[-2, 0, 3]では3だけが残り、[9]になります。負の数を先に二乗すると正の数になるため、元の値で判定することが大切です。",
        mistakes=[
            "v >= 0だと、入力[0, 3]で[0, 9]になり、不要な0が残ります。",
            "v * v > 0で選ぶと、入力[-2, 3]で[4, 9]になり、負の数まで残ります。",
        ],
        wrong="0と負の数を除けているか確かめてください。条件は二乗する前のvに対して判定します。",
    ),
    "PY03-04": dict(
        title="JSONを読み直した値を答える",
        description="左のコードはdataをJSONファイルへ保存し、読み直した値をobservedに入れます。observedに入る値を答えてください。ファイル操作を自分で実装する必要はありません。",
        input="dataは {'日本語': [1, 2]} です。表示されたこの入力について予測します。",
        output="読み直したPythonの値を、辞書またはリストの記法で入力してください。",
        edit="関数は書かず、observedに入る値だけを回答欄へ入力します。",
        sample="例：{'n': 3}をJSONへ保存して読み直すと、Pythonの辞書{'n': 3}になります。",
        hints=[
            "何が変わり、何が変わらないかを考えましょう。ファイルへ保存しても、辞書の中のキーや整数は保たれます。",
            "json.dumpはPythonの値をJSONへ書き、json.loadはJSONからPythonの値を作ります。日本語のキーも読み直せます。",
            "今回は辞書の構造もリストの中身も変わりません。入力のdataと同じ値をPythonの辞書として答えます。",
        ],
        explanation="この入力はJSONで表せる辞書・リスト・整数だけなので、読み直しても{'日本語': [1, 2]}です。ファイルはwithを抜けると閉じます。文字列としてのJSONと、読み込まれたPythonの辞書は区別しましょう。",
        mistakes=[
            "文字列\"{'日本語': [1, 2]}\"を返すと、辞書ではなく文字列になってしまいます。",
            "キーだけのリスト['日本語']では、対応する値[1, 2]が失われます。",
        ],
        wrong="文字列で囲んでいないか、辞書のキーと値の両方を残しているか確認してください。",
        fixed="{'日本語':[1,2]}",
    ),
    "PY02-06": dict(
        title="辞書を関数の引数として渡す",
        description="solveの中にapply(values, factor=1)を定義してください。applyはvaluesの各値をfactor倍したリストを返します。最後にapply(**config)の結果を返してください。",
        input="config：values（数値のリスト）と、省略可能なfactor（倍率）を持つ辞書。factorがなければ1倍です。",
        output="各値をfactor倍したリスト。空リストなら空リストを返します。",
        edit="solveのpassを置き換えます。内部関数applyの定義と、apply(**config)による呼出しを書きます。",
        sample="{'values': [1, 2], 'factor': 3} → [3, 6]。{'values': [1, 2]} → [1, 2]。",
        hints=[
            "まず倍率を受け取る関数を作りましょう。倍率が渡されない場合に備え、factorの既定値を1にします。",
            "apply(values=[1, 2], factor=3)と呼ぶと[3, 6]を返すように、リスト内包表記で各値を掛けます。",
            "**configは辞書のキーを引数名として渡します。内部関数を定義した後でreturn apply(**config)と呼び出します。",
        ],
        explanation="apply(**config)は、辞書のキーvaluesとfactorを同名の引数へ渡します。factorがない場合は定義時の1が使われます。倍率0は有効なので、0を『未指定』として1へ置き換えないようにします。",
        mistakes=[
            "apply(config)では辞書全体がvaluesに渡り、値のリストと倍率に分かれません。",
            "factorに既定値がないと、{'values': [1, 2]}で引数不足になります。",
        ],
        wrong="倍率を省略した場合と倍率0の場合も確かめてください。辞書のキー名とapplyの引数名を揃えます。",
    ),
    "NP05-01": dict(
        title="行ごとの平均を求める",
        description="2次元のNumPy配列xについて、それぞれの行の平均を求め、1次元の配列として返してください。",
        input="x：行と列を持つ数値配列。列は1つ以上あります。numpyはnpとして利用できます。",
        output="1行につき1つの平均を持つNumPy配列。xがN行なら、結果のshape（各軸の要素数）は(N,)です。",
        edit="axis=___の空欄だけを埋めます。axisは、どの方向をまとめるかを指定する引数です。",
        sample="[[1, 3], [5, 7]] → [2, 6]。各行の2つの値を平均します。",
        hints=[
            "最初の行[1, 3]から2、次の行[5, 7]から6を作りたい問題です。行の数は残ります。",
            "axis=0は同じ列の値をまとめます。axis=1は同じ行の列をまとめます。",
            "行ごとの値が必要なので、列をまとめるaxis=1を指定します。",
        ],
        explanation="axis=1で各行の列を平均します。[[1,3],[5,7]]では(1+3)/2=2、(5+7)/2=6となり、shapeは(2,)です。axis=0なら列ごとの[3,5]になるため、目的が異なります。",
        mistakes=[
            "axis=0では[[1,3],[5,7]]が[3,5]になります。求める[2,6]は行ごとの平均です。",
            "keepdims=Trueを足すと[[2],[6]]となり、求める1次元配列とはshapeが異なります。",
        ],
        wrong="行と列のどちらをまとめたか、結果が1次元かを確認してください。動作確認で期待値と自分の値を比べられます。",
    ),
    "NP06-04": dict(
        title="2つの配列の全組合せの積を予測する",
        description="aの各値とbの各値を掛け合わせるコードです。observedに入る2次元の値を、リストの形で答えてください。",
        input="a = np.array([1, 2])、b = np.array([3, 4, 5])。この2つの配列について予測します。",
        output="2行3列の値を、[[...], [...]]の形で入力します。np.arrayや関数の定義は不要です。",
        edit="計算結果だけを回答欄へ入力します。1行目はaの1、2行目はaの2とbの各値の積です。",
        sample="例：a=[2]、b=[10, 20]なら、全組合せの積は[[20, 40]]です。",
        hints=[
            "a[:, None]でaは縦に並ぶ2行1列、b[None, :]でbは横に並ぶ1行3列になります。",
            "サイズ1の軸を広げて掛けます。1行目は1×[3,4,5]、2行目は2×[3,4,5]です。",
            "1行目は[3,4,5]、2行目は[6,8,10]です。2つの行を外側のリストで囲みます。",
        ],
        explanation="(2,1)と(1,3)の配列を掛けると、サイズ1の軸が広がって(2,3)になります。各行でaの値を固定し、bの3つの値を掛けるため、[[3,4,5],[6,8,10]]です。この全組合せの積をここでは外積と呼びます。",
        mistakes=[
            "a*bでは長さ2と3の1次元配列をそのまま合わせられません。",
            "[3,8]のような対応する位置だけの積では、全6通りの組合せが表せません。",
        ],
        wrong="外側のリストが2行、その中が各3要素になっているか確認してください。aの同じ値を1行で使います。",
        fixed="np.array([1,2]),np.array([3,4,5])",
        observation="a = np.array([1, 2])\nb = np.array([3, 4, 5])\nobserved = a[:, None] * b[None, :]",
    ),
    "NP09-05": dict(
        title="学習時の平均と標準偏差で標準化する",
        description="testから学習時のmeanを引き、学習時のstdで割った配列を返してください。0で割らないよう、stdの各値が1e-8未満なら1e-8を使います。testから平均や標準偏差を計算し直しません。",
        input="test：2次元配列。meanとstd：各列について学習データから求めた1次元配列。列数は一致します。",
        output="(test - mean) / np.maximum(std, 1e-8)。testと同じshapeのNumPy配列を返します。",
        edit="solveのpassを処理に置き換えます。入力のmeanとstdをそのまま基準に使ってください。",
        sample="test=[[14, 5]], mean=[10, 1], std=[2, 4] → [[2, 1]]。",
        hints=[
            "列ごとに『平均からどれだけ離れているか』を測ります。まずtest - meanを作ります。",
            "割る前にstdを下限1e-8で置き換えます。std + 1e-8では、十分大きいstdまで変えてしまいます。",
            "np.maximum(std, 1e-8)が分母です。test - meanをこの分母で割って返します。",
        ],
        explanation="学習データで決めた基準を未知データにも使います。テスト側で基準を作り直すと、評価に使う情報を学習側へ混ぜる『データリーク』になります。stdの下限は、一定値だけの列でも0除算しないための処理です。",
        mistakes=[
            "test.mean(axis=0)を使うと、渡された学習時の基準と異なる変換になります。",
            "stdが0の列をそのまま割ると有限な結果になりません。下限を取ってから割ります。",
        ],
        wrong="学習時のmeanとstdを使っているか、stdを加算ではなく下限で処理しているか確認してください。",
    ),
    "PD01-01": dict(
        title="点数が5以上の行を選ぶ",
        description="DataFrameのscore列が5以上の行を選んで返してください。全ての列と、元のindex（行ラベル）を残します。",
        input="df：group・value・score列を持つ表。抽出後も元の行ラベルを使います。",
        output="条件を満たす行だけのDataFrame。行ラベルを0から振り直しません。",
        edit="df['score'] >= ___の空欄を埋めます。",
        sample="indexが0,1,2、scoreが4,7,5なら、残る行のindexは1,2です。",
        hints=[
            "score列を5と比較すると、各行についてTrueかFalseかが得られます。",
            "5も含めるため比較は>=です。locにTrue/Falseの列を渡すと、Trueの行だけが残ります。",
            "比較する基準の値は5です。reset_indexを呼ばなければ元のindexを保持できます。",
        ],
        explanation="df['score'] >= 5で行ごとの条件を作り、locでTrueの行を残します。元の行ラベルはそのままなので、後で元の表と対応付けられます。公開例ではindex 1と3が残ります。",
        mistakes=[
            "score > 5では、scoreがちょうど5の行を除いてしまいます。",
            "reset_index(drop=True)を足すと行ラベルが変わり、値が同じでも条件を満たしません。",
        ],
        wrong="5の行を含めているか、全列と元のindexを残しているか確認してください。値が同じでもindexが違えば不正解になります。",
    ),
    "PD02-04": dict(
        title="欠損値を学習時の平均で埋める",
        description="seriesの欠損値だけをtrain_meanで置き換えたSeriesを返してください。既にある値とindexは変えません。",
        input="series：欠損値を含むことがあるSeries（index付きの1列）。train_mean：学習データから求めた平均値。",
        output="欠損値を埋めたSeries。行数とindexは入力と同じです。",
        edit="return ___を置き換えます。series自身の平均は計算しません。",
        sample="[1, NaN, 5]とtrain_mean=2 → [1, 2, 5]。NaNは欠損値です。",
        hints=[
            "欠損している場所だけを埋めます。欠損がない値や行ラベルには手を加えません。",
            "Seriesのfillnaは、欠損値を指定した値で置き換えたSeriesを返します。",
            "series.fillna(train_mean)を返します。平均は既に引数として渡されています。",
        ],
        explanation="fillnaに学習時の平均を渡すと、欠損した場所だけを補完します。テストデータの平均で埋めると評価対象の情報を基準に使ってしまうため、ここでは外から渡されたtrain_meanを再利用します。",
        mistakes=[
            "series == np.nanでは欠損を検出できません。欠損の確認にはisna、補完にはfillnaを使います。",
            "series.mean()で埋めるとtrain_meanという指定された基準を使えていません。",
        ],
        wrong="既にある値とindexを保ち、欠損だけをtrain_meanで置き換えているか確認してください。",
    ),
    "PD04-06": dict(
        title="右側のキーを確認して左結合する",
        description="leftとrightをid列で左結合したDataFrameを返してください。leftの同じidは複数あっても構いませんが、rightのidは重複してはいけません。mergeのvalidate='many_to_one'を指定してこの条件を確認します。",
        input="left・right：id列を持つDataFrame。左結合はleftの行を残し、対応するrightの値を付ける操作です。",
        output="idで左結合した表。対応する右の行がなければ、その列は欠損値になります。",
        edit="solveのpassを置き換えます。結合キー、結合方法、右のキーの検証を指定してください。",
        sample="leftのid=[1,1,2]、rightのid=[1,2]なら、結合後も左の3行が残ります。",
        hints=[
            "leftの行を残すにはhow='left'です。左右のidを対応させるのでon='id'を使います。",
            "many_to_oneは『左は同じキーが複数でもよく、右は1つ』という指定です。",
            "left.merge(right, on='id', how='left', validate='many_to_one')という形で3つの条件を渡します。",
        ],
        explanation="右に同じidが複数あると、左の1行が右の複数行に対応し、行が増えます。validate='many_to_one'はその状況を例外として検出する指定です。左のidの重複は許すので、左の行を保って情報を付けられます。",
        mistakes=[
            "how='inner'では、rightに対応がないleftの行が消えます。",
            "rightのid=[1,1]にleftのid=[1,1]を結合すると4行になります。右の一意性を確認する目的を意識しましょう。",
        ],
        wrong="on='id'とhow='left'を確認してください。この練習では右の一意性を確認するvalidateも指定します。",
    ),
    "SK01-01": dict(
        title="学習用とテスト用の件数を返す",
        description="初期コードはXとyを学習用75%・テスト用25%に分けています。X_trainの行数とX_testの行数を、この順のタプルで返してください。",
        input="X：1行が1件の特徴量、y：各行の正解ラベル。分割のコードは用意されています。",
        output="(学習用の行数, テスト用の行数)。例えば全20件なら(15, 5)です。",
        edit="最後のreturn ___だけを書き換えます。用意された分割条件は変えません。",
        sample="Xが20行 → 学習用15行、テスト用5行 → (15, 5)。",
        starter="def solve(X, y):\n    X_train, X_test, y_train, y_test = train_test_split(\n        X, y, test_size=0.25, random_state=42, stratify=y\n    )\n    return ___\n",
        hints=[
            "行数はlenで求められます。今回はラベルの値ではなく、分割後のXの件数を返します。",
            "train_test_splitの4戻り値は、学習用X・テスト用X・学習用y・テスト用yの順です。",
            "(len(X_train), len(X_test))というタプルを返します。",
        ],
        explanation="test_size=0.25はテスト用の割合です。random_stateは同じ分割を再現するため、stratify=yはラベルの比率をできるだけ保つための指定です。分割した後で学習側だけに前処理をfitします。",
        mistakes=[
            "(len(X_test), len(X_train))では順序が逆になり、20件なら(5,15)となります。",
            "len(X)を返すと分割前の全件数であり、学習用とテスト用の2つの件数ではありません。",
        ],
        wrong="返す順序は学習用、テスト用です。タプルの2つの値を分割後のXから求めてください。",
    ),
    "SK02-04": dict(
        title="テストを混ぜずに平均を学習する",
        description="初期コードはtrainとtestを混ぜて平均を求めています。fitに渡すデータを直し、学習データtrainだけから求めたStandardScalerのmean_を返してください。",
        input="train・test：同じ列数の2次元配列。fitは、変換に使う平均などの基準を求める処理です。",
        output="各列の学習時の平均mean_。列数と同じ長さの1次元配列です。",
        edit="fit(...)に渡すデータを修正します。testを平均の計算に混ぜないでください。",
        sample="train=[[0],[2]]、test=[[100]]なら、学習時の平均は[1]です。",
        starter="def solve(train, test):\n    scaler = StandardScaler()\n    scaler.fit(np.concatenate([train, test]))  # ここを修正\n    return scaler.mean_\n",
        hints=[
            "testはまだ見ていないデータの代役です。変換の基準を決めるときには使いません。",
            "[0,2]の平均は1ですが、[100]を混ぜると34になります。fitへ渡す範囲が原因です。",
            "scaler.fit(train)に修正します。mean_はfitで求めた列ごとの平均です。",
        ],
        explanation="fit(train)なら、平均は学習データだけから決まります。testまで含めると評価対象の情報が基準に入り、データリークになります。末尾に_があるmean_は、fitで求められた属性です。",
        mistakes=[
            "fit(np.concatenate([train,test]))ではテスト側の大きな値にも平均が引っ張られます。",
            "testにfitを呼び直すと、学習側の基準をテスト側で上書きしてしまいます。",
        ],
        wrong="fitの引数にtestが残っていないか確認してください。求める平均はtrainだけから計算します。",
    ),
    "SK03-05": dict(
        title="学習した直線の係数を取り出す",
        description="LinearRegressionをXとyで学習させ、学習後のcoef_を返してください。coef_は、各特徴量が予測値をどれだけ変えるかを表す係数です。",
        input="X：行がデータ、列が特徴量の2次元配列。y：各行の目的値を持つ1次元配列。",
        output="学習後のcoef_。特徴量の数と同じ長さの配列を返します。",
        edit="solveのpassを置き換え、モデルの作成、fit(X, y)、coef_の取得を書きます。",
        sample="y=2x+1というデータなら、係数coef_は[2]、切片intercept_は1に相当します。",
        hints=[
            "まずLinearRegression()でモデルを作ります。まだデータを渡す前なので、係数は決まっていません。",
            "model.fit(X, y)がXとyの関係を学習します。学習後にmodel.coef_を参照できます。",
            "model = LinearRegression().fit(X, y)とし、model.coef_を返します。",
        ],
        explanation="fitでXとyの関係を学習し、係数がcoef_に保存されます。例えばy=2x+1では、xが1増えるとyが2増えるので係数は2です。切片はintercept_という別の属性です。",
        mistakes=[
            "fit前にcoef_を読むと、まだ係数がないため属性エラーになります。",
            "intercept_を返すと、傾きではなく切片です。y=2x+1なら1を返してしまいます。",
        ],
        wrong="fit(X, y)の後でcoef_を返しているか、intercept_や予測値と取り違えていないか確認してください。",
    ),
    "PT02-02": dict(
        title="転置したTensorも1次元にする",
        description="初期コードは、転置したTensorでエラーになることがあります。全ての要素を1次元に並べて返すように修正してください。",
        input="x：数値のTensor。転置により、見た目の順序とメモリ上の並びが一致しない場合があります。",
        output="xを見た目の行の順に読み、1次元に並べたTensor。",
        edit="x.view(-1)を見直します。関数名と引数はそのままにします。",
        sample="[[0,4,8],[1,5,9]]を1次元にすると[0,4,8,1,5,9]です。",
        hints=[
            "転置は要素の見え方を変えますが、メモリ上の並びまで作り直すとは限りません。",
            "viewは元の並び方を使える場合にだけ変形できます。reshapeは必要な場合にコピーを作れます。",
            "x.reshape(-1)に変えます。x.contiguous().view(-1)のように並びを整えてからviewする方法もあります。",
        ],
        explanation="転置後のTensorは、要素へ進む間隔（stride）が単純な1次元の並びに合わないことがあります。reshapeは必要なら連続したコピーを作るので、同じ見た目の順序で1次元にできます。viewとreshapeは、軸の入替えそのものとは別の操作です。",
        mistakes=[
            "転置したxへview(-1)を使うと、stride条件を満たせずRuntime Errorになる場合があります。",
            "flattenの前にxを転置し直すと、並べる要素の順序も変わってしまいます。",
        ],
        wrong="値の順序を変えず、転置済みのTensorでも変形できる操作を選んでください。",
    ),
    "PT07-04": dict(
        title="前の勾配を消して2回更新する",
        description="w²を小さくするようにSGDでwを2回更新します。初期コードは前の勾配を残しているため、2回目の更新が大きくなりすぎます。各回のbackward前に勾配を消し、更新後のwを返してください。",
        input="initial：wの初期値。lr：1回の更新に使う学習率。勾配はw²の傾きで、この場合は2wです。",
        output="2回更新した後のw。最後のreturnは用意されています。",
        edit="forループの中で、backwardより前に必要な1行を追加します。",
        sample="initial=2、lr=0.1なら、2 → 1.6 → 1.28となります。",
        hints=[
            "backwardは傾きを計算し、stepはその傾きでwを更新します。前回の傾きは自動では消えません。",
            "前の勾配が残ると2回目は4+3.2=7.2を使い、wが0.88まで下がります。毎回、今のwの傾きだけを使う必要があります。",
            "ループの先頭にo.zero_grad()を置きます。zero_grad → backward → stepの順です。",
        ],
        explanation="SGDはwからlr×勾配を引きます。最初は2-0.1×4=1.6、次は1.6-0.1×3.2=1.28です。zero_gradを省くと前の4が加算され、2回目の更新を誤ります。最後のdetachは、計算の履歴から切り離した値を返す処理です。",
        mistakes=[
            "zero_gradをループの外だけで呼ぶと、2回目には1回目の勾配が残ります。",
            "backwardの後でzero_gradすると、stepが使う勾配まで消してしまいます。",
        ],
        wrong="勾配を消す位置を確認してください。各回のbackwardより前、ループの中に置きます。",
    ),
    "PT10-06": dict(
        title="復元後のモデルを推論モードにする",
        description="重みの状態を読み込んでも、モデルの学習・推論モードは切り替わりません。初期コードのbを推論モードに直し、b.trainingを返してください。",
        input="p：Dropoutの割合。Dropoutは学習時だけ一部の値を0にする処理です。bは既に用意されています。",
        output="推論モードならtrainingはFalseになります。True/Falseの値を返します。",
        edit="b.train()の行を修正します。モデルの作成と読込、最後のreturnはそのまま使えます。",
        sample="model.train()の後はtraining=True、model.eval()の後はtraining=Falseです。",
        hints=[
            "state_dictはモデルのパラメータ等の状態です。trainingというモードのフラグはその中に含まれません。",
            "推論モードへ切り替えるメソッドはevalです。load_state_dictの後でも明示的に呼びます。",
            "b.train()をb.eval()へ変えます。最後のreturn b.trainingでFalseを確認します。",
        ],
        explanation="eval()はモデルと子の層を推論モードへ切り替えます。state_dictの読込とは役割が異なります。この例はDropoutだけなので保存する学習済み重みはありませんが、モードが読込とは独立であることを確認できます。",
        mistakes=[
            "load_state_dictだけではb.trainingはTrueのままです。",
            "b.evalと書くだけでは呼び出されません。括弧を付けてb.eval()とします。",
        ],
        wrong="load_state_dictの後でb.eval()を呼んでいるか確認してください。返すのは文字列ではなくbooleanのFalseです。",
    ),
}


def improve(problem, make_case, exercise, module, effective_seed):
    lesson = LESSONS.get(problem["id"])
    if not lesson:
        return problem
    p = problem | {
        k: lesson[k] for k in ("title", "description", "hints", "explanation")
    }
    p.update(
        version_id=p["id"] + "@2",
        content_version=2,
        input_conditions=lesson["input"],
        output_conditions=lesson["output"],
        common_mistakes=lesson["mistakes"],
    )
    if "starter" in lesson:
        p["starter_code"] = lesson["starter"]
    p["presentation"] = dict(
        edit_instruction=lesson["edit"],
        worked_example=lesson["sample"],
        feedback=dict(
            wrong=lesson["wrong"],
            runtime="入力の型と、表示されたエラーの行を確認してください。",
        ),
    )
    if "fixed" in lesson:
        # A prediction is one specified observation, not an implementation for
        # arbitrary hidden inputs. v1 retains its original four cases.
        p["public_tests"] = [
            make_case(exercise, module, lesson["fixed"], effective_seed)
        ]
        p["hidden_tests"] = []
        p["presentation"]["answer"] = dict(
            mode="fixed", wrap_array=problem["id"] == "NP06-04"
        )
        if "observation" in lesson:
            p["example"] = lesson["observation"]
        else:
            p["example"] = "data = {'日本語': [1, 2]}\n" + p["example"]
    if problem["id"] == "NP05-01":
        p["public_tests"][0] = make_case(
            exercise, module, "np.array([[1.,3.],[5.,7.]])", effective_seed
        )
    return p
