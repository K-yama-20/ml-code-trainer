# 教材の作り方

基本の原本は`content/catalog.py`です。標準の概念には、学習操作の異なる6つのExerciseを記述します。PY01・PY02・PY03・NP01・NP02・NP03・NP04・NP05・NP06の確定文面・表示例・ヒント・模範解答は、それぞれ`content/iteration.json`・`content/arguments.json`・`content/files.json`・`content/arrays.json`・`content/indexing.json`・`content/reshaping.json`・`content/axis_permutation.json`・`content/reductions.json`・`content/broadcasting.json`に置きます。別入力と採点条件は、対応するPythonファイルに置きます。値だけを変えたコピーは独立問題に数えません。

コンパイラは288問と、seedで再現できるVariantを生成します。標準はGuided・Partial・Independentの各2問です。PY01・PY02・PY03・NP01・NP02・NP03・NP04・NP05・NP06は原本の順で各18問を出題し、ステージには各6問を割り当てます。PY02では `result =` に続く呼び出し、`return` に続く式、関数定義全体を使い分けます。関数定義の問題では、表示用の呼び出しを編集範囲から外し、採点時に同じ関数を別の引数で呼び出します。

NP01は18問とも、固定の入力に対する式を `result =` の右側へ書きます。ステージは第1〜6問、第7〜12問、第13〜18問に割り当てます。明示されたdtypeと、第14問の入力に応じたdtypeは厳密に比較し、第14〜16問は入力の値・shape・dtypeを保護します。固定の0次元・空配列の属性問題では、別入力でも期待値が同じになるため、属性の使用条件 `attr:` と定数の直接代入の検査を併用します。

NP02も全問で式を書きます。既存IDのステージを引き継ぎながら各ステージ6問とし、出題は原本の順を保ちます。別入力で有効な位置指定を使い、列の次元の保持、重複する列、条件の境界、該当なし、NaNのみを確認します。第12問はboolのdtypeも比較します。

NP03は要素の順番とshapeを比較し、viewも正答として扱います。実行契約の `result_type: array` では0次元配列のshapeも保持し、通常の数値と区別します。旧版は従来の形式を使います。推論サイズの使用条件は `literal:-1`、禁止条件は `not:literal:-1` で検査します。第18問は全ケースでバッチ数0とし、高さ・幅を変えて検証します。

NP04は出力の各座標に対応する入力座標から期待配列を作り、shapeに加えて要素の対応も比較します。別入力では軸の長さと値を変え、第4問ではaxesも変えます。第15問のAPI使用回数は `call-count:moveaxis:1` でAST上の呼び出しを検査します。第18問はバッチ数0を保ち、高さ・幅・チャネル数を変更します。

NP05はPythonのsum・statisticsと行列の走査から期待値を作ります。スカラー出力は `result_type: number`、配列出力は `result_type: array` で区別します。明示されたオプションは `call-keywords:` で対象APIと値を検査し、単純な変数・辞書経由も許容します。第17問のみ入力の値・shape・dtypeの維持を必須とし、空の行を集約する第18問では列数を変えます。

NP06は座標ごとの値の計算から期待配列を作り、入力の値・shape・dtypeを保護します。軸の追加方法は制限せず、第17問だけbroadcast_toの呼び出しを検査します。第18問では特徴ごとの差の二乗和を独立に計算します。問題の旧版への移行時には、表示用の型情報もdisplay.jsonに保持します。

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
npx playwright test -c playwright.concrete.config.ts arguments.spec.ts
```

`private.json`には解答と非公開ケースを保存し、`public.json`はそれらを除いた教材です。APIも同じフィルターを適用します。Webのimportやpublicディレクトリにprivateファイルを入れないでください。期待値oracleの実行は信頼されたGit原本のコンパイル時だけです。FastAPIはユーザーコードをexecしません。

リストとタプルの表示には、比較用の値とは別に `tuple_paths` を使います。期待値は `pack_expected()` で実際のPython型から記録し、コンパイル時に `display.json` へ問題版・seedごとに保存します。採点用のprivate catalogと旧版は変更せず、公開ケースの型情報だけを配信します。JSON原本でタプルを表せない場合は、明示された解答型の契約に従って生成し、値の形から推測しません。型情報のない過去の提出結果はそのまま表示し、再実行を案内します。

CIのnative検証は2つのseedで全288問の全ケースを実行し、模範解答の合格、誤答の不合格、件数・形式配分・再現性を確認します。提供入力・模範解答・呼び出しを結合した完成コードはASTで検査し、表示例の値を最初の公開ケースと照合します。Pythonコード内の全角演算子や数学記号はエラーになります。文章・コメント・文字列には使用できます。ヒントや解説に複数行のPythonを書く場合は ```python のコードフェンスで囲んでください。Deep DiveとCode Readingのコード、ケースの設定と引数、生成済みファイル、バージョンとseedの整合性も同じコマンドで確認します。空入力が有効なAPIでは空入力、無効なAPIでは最小サイズ、定数・極端値・欠損などの境界を使います。数値許容誤差は1e-5です。dtypeを学ぶ問題はdtypeも厳密比較します。

初回リリース後の変更はバージョンを上げてください。旧private catalogを`content/versions/`へ保存するとAPIはexact version IDで取得できます。旧問題・採点仕様を破壊せず履歴を維持します。DB同期も既存versionの内容変更を拒否します。

読解用コードは`content/reading/`、設問は`content/activities.py`です。3つのプロジェクトはCLIとして実行可能で、pytestが実際に起動して学習・保存・推論まで確認します。Deep Diveと読解の設問は選択式で確定的に判定し、結果をactivity_progressに保存します。

今後の教材改善では、各概念の説明・誤答例をさらに具体化し、著者とは別の教育レビューを加えることを推奨します。現状の自動検証は教師による難易度レビューを代替しません。
