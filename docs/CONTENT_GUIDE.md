# 教材の作り方

基本の原本は`content/catalog.py`です。概念の一覧・順序・前提関係と、18問ドリル化する前の6問のExerciseを記述します。PY01・PY02・PY03・NP01・NP02・NP03・NP04・NP05・NP06・NP07・NP08の確定文面・表示例・ヒント・模範解答は、それぞれ`content/iteration.json`・`content/arguments.json`・`content/files.json`・`content/arrays.json`・`content/indexing.json`・`content/reshaping.json`・`content/axis_permutation.json`・`content/reductions.json`・`content/broadcasting.json`・`content/combining.json`・`content/conditional.json`に置きます。別入力と採点条件は、対応するPythonファイルに置きます。値だけを変えたコピーは独立問題に数えません。

コンパイラは30概念・540問と、seedで再現できるVariantを生成します。全概念が原本の順で各18問を出題し、Guided・Partial・Independentに各6問を割り当てます。PY02では `result =` に続く呼び出し、`return` に続く式、関数定義全体を使い分けます。関数定義の問題では、表示用の呼び出しを編集範囲から外し、採点時に同じ関数を別の引数で呼び出します。

NP01は18問とも、固定の入力に対する式を `result =` の右側へ書きます。ステージは第1〜6問、第7〜12問、第13〜18問に割り当てます。明示されたdtypeと、第14問の入力に応じたdtypeは厳密に比較し、第14〜16問は入力の値・shape・dtypeを保護します。固定の0次元・空配列の属性問題では、別入力でも期待値が同じになるため、属性の使用条件 `attr:` と定数の直接代入の検査を併用します。

NP02も全問で式を書きます。既存IDのステージを引き継ぎながら各ステージ6問とし、出題は原本の順を保ちます。別入力で有効な位置指定を使い、列の次元の保持、重複する列、条件の境界、該当なし、NaNのみを確認します。第12問はboolのdtypeも比較します。

NP03は要素の順番とshapeを比較し、viewも正答として扱います。実行契約の `result_type: array` では0次元配列のshapeも保持し、通常の数値と区別します。旧版は従来の形式を使います。推論サイズの使用条件は `literal:-1`、禁止条件は `not:literal:-1` で検査します。第18問は全ケースでバッチ数0とし、高さ・幅を変えて検証します。

NP04は出力の各座標に対応する入力座標から期待配列を作り、shapeに加えて要素の対応も比較します。別入力では軸の長さと値を変え、第4問ではaxesも変えます。第15問のAPI使用回数は `call-count:moveaxis:1` でAST上の呼び出しを検査します。第18問はバッチ数0を保ち、高さ・幅・チャネル数を変更します。

NP05はPythonのsum・statisticsと行列の走査から期待値を作ります。スカラー出力は `result_type: number`、配列出力は `result_type: array` で区別します。明示されたオプションは `call-keywords:` で対象APIと値を検査し、単純な変数・辞書経由も許容します。第17問のみ入力の値・shape・dtypeの維持を必須とし、空の行を集約する第18問では列数を変えます。

NP06は座標ごとの値の計算から期待配列を作り、入力の値・shape・dtypeを保護します。軸の追加方法は制限せず、第17問だけbroadcast_toの呼び出しを検査します。第18問では特徴ごとの差の二乗和を独立に計算します。問題の旧版への移行時には、表示用の型情報もdisplay.jsonに保持します。

NP07は配列を結合する軸と、stackで新しく追加する軸を区別して検証します。第4問はaxis=Noneを位置引数でも指定できます。第17問は左右それぞれが空の場合と両方が空の場合を扱います。第18問は2要素のタプルとして採点し、特徴量とラベルのshape・値・順序を比較します。

NP08はマスクの真偽、しきい値と等しい値、列ごとの上下限、NaNと正負の無限大を検証します。第3・12問はdtypeも比較します。第18問では実行中だけゼロ除算と無効演算をエラーにし、分母0の位置で除算を行った解答を検出します。

NP09・PD01〜PD04・SK01〜SK04・PT01〜PT10の19概念は、共通コンパイラ`content/ordered.py`で生成します。各概念はJSON（タイトル・問題文・import・表示入力・ヒント・模範解答・ID・版・ステージ）と、同名のPythonファイル（`ALTERNATIVES`・`ORACLES`・`RULES`・`WRONG`）の組です。原本は`normalization`・`selection`・`missing`・`groupby`・`merging`・`splitting`・`scaling`・`estimators`・`metrics`・`tensors`・`tensor_shapes`・`tensor_ops`・`autograd`・`nn_modules`・`losses`・`training`・`data_loading`・`inference`・`checkpoints`です。新しい概念は`scripts/compile_content.py`の`AUTHORED_MODULES`に追加します。

期待値は模範解答ではなく、各問の`ORACLES`（素のPython・NumPyの式や更新則の手計算）から作ります。最初のケースは表示入力と同じで、別入力は2つ以上用意します。表示入力の代入のうちpackできる値は入力変数、nn.Moduleなどpackできない値は`globals`として渡します。結果の型（配列・数値・タプル・リスト・辞書・文字列）は表示入力の期待値から`result_type`に設定し、PyTorchはdtypeも比較します。`RULES`では問題文で指定したAPIのAST条件（`required`）、dtype比較、入力保護、`comparison`、`strict_division`・`strict_overflow`を指定します。

`comparison: relative` は絶対誤差の下限を外した相対誤差1e-5の比較です。NP09第11・12問のように`1e-16`程度の値を0に丸める解答を検出します。`strict_overflow` は実行中だけNumPyのオーバーフローをエラーにし、安定な式を求める問題（シグモイド・logaddexp・softmax・log-sum-exp・log-softmax）で、飽和した値がたまたま一致する素朴な式を誤答にします。

検証では、各問の`WRONG`にある代表誤答と、表示例の結果を直接代入した解答がすべて不合格になること、ケースの期待値がすべて同じではないことも確認します。モードや状態を学ぶPyTorchの問題では、出力値・統計量・開始時のモードなどケースごとに変わる値を結果に含めます。

PY03の書き込み問題は、固定の入力コードと最後の読み取りコードの間に処理を書きます。採点では問題定義の読み取り式を使い、実際のファイル内容を検証します。`TemporaryDirectory` はケースごとに作成し、Pythonエラー時にも削除します。Pathの出力は型を保って比較します。公開・非公開ケースの `comparison` に `json` を指定するとJSON文字列の内容を比較し、`json_unicode` は日本語の表示も確認します。指定がないケースは書式を含めて比較するため、インデント幅・キー順を学ぶ問題では指定を省きます。

```powershell
uv run --project apps/api python scripts/compile_content.py
uv run --project apps/api python scripts/validate_content.py
npm run test:browser-content
```

教材だけを変更した回は、コンパイル後に対象の概念を軽量検証できます。共通UI・採点・出題の変更時と、教材更新が3〜5回たまった時は、代表問題をブラウザで確認します。

```powershell
uv run --project apps/api python scripts/validate_content.py --concept PY01
uv run --project apps/api python -m pytest apps/api/tests/test_arguments.py -q
uv run --project apps/api python -m pytest apps/api/tests/test_files.py -q
uv run --project apps/api python scripts/validate_content.py --concept NP01
uv run --project apps/api python scripts/validate_content.py --concept NP02
uv run --project apps/api python scripts/validate_content.py --concept NP03
uv run --project apps/api python scripts/validate_content.py --concept NP04
uv run --project apps/api python scripts/validate_content.py --concept NP05
uv run --project apps/api python scripts/validate_content.py --concept NP06
uv run --project apps/api python scripts/validate_content.py --concept NP07
uv run --project apps/api python scripts/validate_content.py --concept NP08
uv run --project apps/api python scripts/validate_content.py --concept PT07
uv run --project apps/api python -m pytest apps/api/tests/test_authored_drills.py -q
npx playwright test -c playwright.concrete.config.ts arguments.spec.ts
```

`private.json`には解答と非公開ケースを保存し、`public.json`はそれらを除いた教材です。APIも同じフィルターを適用します。Webのimportやpublicディレクトリにprivateファイルを入れないでください。期待値oracleの実行は信頼されたGit原本のコンパイル時だけです。FastAPIはユーザーコードをexecしません。

リストとタプルの表示には、比較用の値とは別に `tuple_paths` を使います。期待値は `pack_expected()` で実際のPython型から記録し、コンパイル時に `display.json` へ問題版・seedごとに保存します。採点用のprivate catalogと旧版は変更せず、公開ケースの型情報だけを配信します。JSON原本でタプルを表せない場合は、明示された解答型の契約に従って生成し、値の形から推測しません。型情報のない過去の提出結果はそのまま表示し、再実行を案内します。

CIのnative検証は2つのseedで全540問の全ケースを実行し、模範解答の合格、誤答の不合格、件数・形式配分・再現性を確認します。提供入力・模範解答・呼び出しを結合した完成コードはASTで検査し、表示例の値を最初の公開ケースと照合します。Pythonコード内の全角演算子や数学記号はエラーになります。文章・コメント・文字列には使用できます。ヒントや解説に複数行のPythonを書く場合は ```python のコードフェンスで囲んでください。Deep DiveとCode Readingのコード、ケースの設定と引数、生成済みファイル、バージョンとseedの整合性も同じコマンドで確認します。空入力が有効なAPIでは空入力、無効なAPIでは最小サイズ、定数・極端値・欠損などの境界を使います。数値許容誤差は1e-5です。dtypeを学ぶ問題はdtypeも厳密比較します。

初回リリース後の変更はバージョンを上げてください。旧private catalogを`content/versions/`へ保存するとAPIはexact version IDで取得できます。旧問題・採点仕様を破壊せず履歴を維持します。DB同期も既存versionの内容変更を拒否します。

読解用コードは`content/reading/`、設問は`content/activities.py`です。3つのプロジェクトはCLIとして実行可能で、pytestが実際に起動して学習・保存・推論まで確認します。Deep Diveと読解の設問は選択式で確定的に判定し、結果をactivity_progressに保存します。

今後の教材改善では、各概念の説明・誤答例をさらに具体化し、著者とは別の教育レビューを加えることを推奨します。現状の自動検証は教師による難易度レビューを代替しません。
