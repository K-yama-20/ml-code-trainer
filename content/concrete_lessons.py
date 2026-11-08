"""Human-authored pilot copy. Each goal is tied to its actual provided example."""

TASKS = {
    "PY01-01": "valuesから正の数だけを選び、二乗したリストをresultに代入してください。0と負の数は含めず、元の順序を保ちます。",
    "PY02-06": "apply_configの中にapply(values, factor=1)を定義してください。applyは各値をfactor倍したリストを返します。最後にapply(**config)を呼び、その結果を返してください。",
    "PY03-04": "dataをJSONファイルに保存し、読み直すコードです。observedに入るPythonの辞書を答えてください。",
    "NP05-01": "配列xの各行の平均を計算し、1次元のNumPy配列resultに代入してください。",
    "NP05-03": "配列xの各列の合計を計算し、1次元のNumPy配列resultに代入してください。",
    "NP05-05": "画像データxの、画像ごと・チャネルごとの平均を求めてください。軸は画像数、チャネル数、高さ、幅の順です。高さと幅の2軸を平均し、2次元のNumPy配列resultに代入します。",
    "NP06-04": "aの各値とbの各値を掛け合わせるコードです。observedに入る2次元の値を[[...], [...]]の形で答えてください。",
    "PD01-01": "表dfからscoreが5以上の行を選び、resultに代入してください。すべての列と元の行ラベルを残します。",
    "PD02-04": "seriesの欠損値（NaN）だけをtrain_meanで埋め、resultに代入してください。元の値と行ラベルは保ちます。",
    "PD04-06": "leftのすべての行を残し、idが一致するrightの列を追加してください。結合時にrightのidが重複しないことをvalidate='many_to_one'で確認し、表をresultに代入します。",
    "SK02-04": "初期コードはtrainとtestを混ぜて平均を求めています。trainだけでStandardScalerを学習させ、そのmean_をresultに代入してください。",
    "SK03-05": "Xからyを予測するLinearRegressionを学習させ、学習後のcoef_をresultに代入してください。coef_は各特徴量に掛ける係数です。",
    "PT02-02": "転置されたTensor xの要素を、現在の並び順で1次元にしてください。初期コードのviewではエラーになる入力も扱えるように直し、resultに代入します。",
    "PT05-03": "Twiceは入力を2倍するモデルです。forwardのpassを置き換え、受け取ったxを2倍したTensorを返してください。下の呼び出しでresultを確認します。",
    "PT07-04": "w²を小さくするようにSGDでwを2回更新します。初期コードは前の勾配を残しています。各回のbackward前に勾配を消し、更新後のwをresultに代入してください。",
}


def refine(p):
    pid = p["id"]
    p["workspace"]["task"] = TASKS[pid]
    if pid == "NP05-01":
        p.update(
            title="各行の平均を計算する",
            output_conditions="行ごとに1つの平均を持つ1次元のNumPy配列。表示例では約[3.333333, 2.666667]です。",
        )
        p["hints"] = [
            "xは2行3列です。各行を1つの平均にまとめるので、結果は2つの数値になります。",
            "meanで平均を計算できます。axis=0は各列をまとめ、axis=1は各行の中の値をまとめます。",
            "空欄には1を入力します。x.mean(axis=1)で各行の平均になります。",
        ]
        p["explanation"] = (
            "1行目は(1+4+5)/3、2行目は(2+10-4)/3です。axis=1は各行の列をまとめる指定なので、結果は2つの平均を持つ1次元配列になります。"
        )
        p["common_mistakes"] = [
            "axis=0では3列それぞれの平均[1.5, 7, 0.5]になり、行ごとの平均とは異なります。",
            "keepdims=Trueではshapeが(2,1)になり、求める(2,)と異なります。",
        ]
        p["presentation"]["feedback"]["wrong"] = (
            "axis=0では各列を平均します。今回は各行を1つの数値にまとめたいので、axisと結果の要素数を確認しましょう。"
        )
    elif pid == "NP05-03":
        p.update(
            title="各列の合計を計算する",
            output_conditions="列ごとに1つの合計を持つ1次元のNumPy配列。表示例では[9, 12]です。",
        )
        p["hints"] = [
            "1列目は1+3+5、2列目は2+4+6です。結果には列の数だけ値が残ります。",
            "np.sumで合計できます。同じ列にある別の行の値をまとめる指定はaxis=0です。",
            "result = np.sum(x, axis=0)という形で書けます。",
        ]
        p["explanation"] = (
            "axis=0は行の軸をまとめます。表示例では1+3+5=9、2+4+6=12となり、2列に対応する[9,12]が残ります。"
        )
        p["common_mistakes"] = [
            "axis=1では行ごとの[3,7,11]になります。",
            "axisを省略すると全要素の合計21になり、列の区別がなくなります。",
        ]
        p["presentation"]["feedback"]["wrong"] = (
            "結果は列の数だけ必要です。全体の合計や行ごとの合計になっていないか、axisを確認してください。"
        )
    elif pid == "NP05-05":
        p.update(
            title="画像ごと・チャネルごとの平均を計算する",
            output_conditions="shapeが(N,C)のNumPy配列。xの軸は順に画像数N、チャネル数C、高さH、幅Wです。表示例は[[1.5,5.5],[9.5,13.5]]です。",
        )
        p["hints"] = [
            "xは2枚の画像、それぞれ2チャネル、高さ2・幅2です。画像とチャネルは区別したまま、各2×2領域を1つの数値にまとめます。",
            "meanのaxisには複数の軸をタプルで指定できます。高さは軸2、幅は軸3です。",
            "result = x.mean(axis=(2, 3))で、画像数とチャネル数の2軸だけが残ります。",
        ]
        p["explanation"] = (
            "最初の画像の最初のチャネルは[[0,1],[2,3]]なので平均1.5です。同様に各領域を平均すると[[1.5,5.5],[9.5,13.5]]になります。N,Cを残し、H,Wの2軸をまとめています。"
        )
        p["common_mistakes"] = [
            "axis=(0,1)では画像とチャネルを混ぜてしまいます。",
            "axis=3だけでは高さの軸が残り、結果が3次元になります。",
        ]
        p["presentation"]["feedback"]["wrong"] = (
            "画像とチャネルの区別を残せていますか。平均するのは高さ・幅の軸2と3で、結果は2次元です。"
        )
    elif pid == "PT05-03":
        p.update(
            title="forwardで入力を2倍にする",
            output_conditions="入力xと同じshapeで、すべての値が2倍のTensor。",
            starter_code="class Twice(nn.Module):\n    def forward(self, x):\n        # 入力を2倍したTensorを返す\n        pass\n\nresult = Twice()(x)\n",
        )
        p["presentation"]["edit_instruction"] = (
            "forwardメソッドのpassを、処理とreturnに置き換えてください。入力と末尾の呼び出しは用意されています。"
        )
        p["hints"] = [
            "Twice()(x)でモデルを呼ぶと、forwardのxに入力Tensorが渡ります。今回は重みや学習は不要です。",
            "Tensorに2を掛けると、各要素が2倍になります。shapeは変わりません。",
            "forward内にreturn x * 2と書きます。最後のresult = Twice()(x)がその戻り値を受け取ります。",
        ]
        p["explanation"] = (
            "nn.Moduleのインスタンスを関数のように呼ぶとforwardが実行されます。x*2は各要素を2倍にし、そのTensorをreturnで返します。クラスとメソッドはこの問題の学習対象なので残しています。"
        )
        p["common_mistakes"] = [
            "x*2を計算してもreturnがないと、結果がNoneになります。",
            "Twice.forward(x)ではインスタンスを通さず、selfとxの引数が対応しません。",
        ]
        p["presentation"]["feedback"]["wrong"] = (
            "forwardがTensorを返せているか確認してください。print(x*2)だけでは、戻り値はNoneになります。"
        )
    elif pid == "SK02-04":
        p["starter_code"] = (
            "result = StandardScaler().fit(np.vstack([train, test])).mean_\n"
        )
        p["presentation"]["edit_instruction"] = (
            "fitに渡すデータをtrainだけに直してください。入力のtrainとtestは編集できません。"
        )
        p["explanation"] = (
            "trainの列平均は[2,4]です。testの[100,102]を混ぜると、評価に使うデータの情報が学習へ入ってしまいます。StandardScaler().fit(train).mean_なら学習データだけから平均が求まります。"
        )
    if pid == "PT02-02":
        p["presentation"]["edit_instruction"] = (
            "result = x.view(-1)のviewを見直してください。転置された入力xはそのまま使います。"
        )
    elif pid == "PT07-04":
        p["presentation"]["edit_instruction"] = (
            "forループの各回で、backwardの前に勾配を消す処理を追加してください。"
        )
    # Keep all surfaced copy aligned with the new workspace, including API clients.
    p["description"] = p["workspace"]["task"]
    p["presentation"]["worked_example"] = ""  # Actual example is now executable code.
