# ML Code Trainer

**Write. Run. Understand.** 機械学習のコードを、読む力に変える。

React / TypeScript / Vite と FastAPI で動く学習アプリです。MonacoでPythonを書き、Pyodideの公開テストを実行し、提出・解説・履歴・復習へ進めます。教材は5分野30概念、Drill 540問（全概念18問ずつ）、Deep Dive 12課題、Code Reading 3プロジェクト（各8設問）です。

## すぐに起動する

Node.js 24、Python 3.12以上、[uv](https://docs.astral.sh/uv/)を使用します。Windows PowerShellではリポジトリのルートで実行してください。

```powershell
npm ci
uv sync --project apps/api --frozen --python 3.13
Copy-Item .env.example .env
```

ターミナル1：

```powershell
uv run --project apps/api python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
```

ターミナル2：

```powershell
npm run dev
```

[アプリ](http://127.0.0.1:5173/) / [ホーム](http://127.0.0.1:5173/home) / [API仕様](http://127.0.0.1:8000/docs)

外部アカウントがなくてもローカルゲストで使えます。認証用のランダムトークンはHttpOnly Cookie、履歴・設定・セッションはSQLiteの`trainer.db`、下書きの一時保存はユーザーID別のIndexedDBです。DBとCookieを保管すれば再開できます。このモードは開発用です。認証情報を含む`.env`と学習DBはGit管理しません。

Pyodideの初回起動とパッケージ取得にはインターネット接続が必要です。PyTorchはModal設定が必要で、未設定時は明示的に実行エラーを表示します。Independentのブラウザ結果は**暫定**として保存し、正式習得には数えません。

## 実装した学習体験

- 全指定ルート、ダーク／ライトテーマ、PC・タブレット・スマートフォン用レイアウト。
- Monacoの編集、Undo/Redo、サイズ調整、行エラー、実行・提出のショートカット、集中モード。
- opaque originのsandbox iframe内でPyodide Workerを作成。毎回新しいWorker、5秒タイムアウト、中止、出力制限、古いコードの結果を区別。
- RunとSubmitの分離。公開テスト、正式検証、解答閲覧・ヒントの記録、冪等な提出。
- Daily / Concept / Review / Custom、異なる2ファミリーによる段階進行、1→3→7→14→30日の復習。
- 下書きの1秒ローカル保存・5秒API同期、revisionの比較更新、競合時のコード保持。
- 数値・shape・dtype・NaN・Inf・AST・勾配やモデル更新を含むテスト。
- 読解のファイルツリー、行番号、定義ジャンプ、確定的な設問採点と保存。
- Supabase匿名認証・Identity Linking、Google・メール認証UI、署名／issuer／audience／期限検証。
- PostgreSQL migration、RLS、非公開テストのprivate schema、独立Worker、Modal provider。

## 検証コマンド

```powershell
npm run typecheck
npm run lint
npm run test
npm run build
uv run --project apps/api ruff check --config apps/api/pyproject.toml apps/api content scripts
uv run --project apps/api python -m pytest apps/api/tests -q
uv run --project apps/api python scripts/validate_content.py
npx playwright install chromium
npm run test:e2e
npm run test:browser-content
npm audit
```

全件Pyodide検証は120問の公開・非公開ケースを、テスト時だけ模範解答とともに本番のブラウザ実行関数へ渡します。通常のWebアプリへ非公開テストや模範解答を配信する機能ではありません。数分以上かかるため通常E2Eとは分けています。

## 構成

```text
apps/web/src/       UI・Monaco・Pyodide・IndexedDB
apps/api/app/       API・認証・DB・進捗・比較器・独立Worker
content/catalog.py 基本の教材原本
content/iteration.json PY01「内包表記とイテレーション」18問の原本
content/arguments.json PY02「引数・args・kwargs」18問の原本
content/files.json PY03「パス・JSON・ファイル」18問の原本
content/arrays.json NP01「配列・shape・dtype」18問の原本
content/indexing.json NP02「インデックスと条件抽出」18問の原本
content/reshaping.json NP03「reshapeと次元の追加」18問の原本
content/axis_permutation.json NP04「軸の入れ替え」18問の原本
content/reductions.json NP05「集約・axis・keepdims」18問の原本
content/broadcasting.json NP06「Broadcasting」18問の原本
content/combining.json NP07「配列の結合」18問の原本
content/conditional.json NP08「条件演算とclip」18問の原本
content/ordered.py 18問ドリル（NP09・PD01〜PD04・SK01〜SK04・PT01〜PT10）の共通コンパイラ
content/normalization.json NP09「正規化と数値安定性」、selection/missing/groupby/merging.json PD01〜PD04、
  splitting/scaling/estimators/metrics.json SK01〜SK04、tensors/tensor_shapes/tensor_ops/autograd/
  nn_modules/losses/training/data_loading/inference/checkpoints.json PT01〜PT10 の原本（各18問）
content/compiled/  バージョン固定の公開／非公開教材、seed 42/99
content/reading/   実行可能な3つのPythonプロジェクト
scripts/           教材コンパイル・全件検証・DB同期・OpenAPI型生成
supabase/migrations/ PostgreSQLとRLS
tests/e2e/         Playwright
docs/              設計・運用・制約・検証記録
```

依存は`package-lock.json`と`apps/api/uv.lock`に固定しています。教材はアプリのビルド対象ディレクトリの外にあります。公開用ビルドにprivate catalogをコピーしないでください。

## 外部サービス

Supabase、OAuth、メール、Modal、PostgreSQLの設定・migration・Worker起動は[DEPLOYMENT.md](docs/DEPLOYMENT.md)を参照してください。接続情報を捏造するフォールバックや、本番でローカルPythonを実行するアダプターはありません。

| 環境変数 | 用途 |
|---|---|
| APP_ENV / DATABASE_URL | developmentのSQLite、productionのPostgreSQL。PostgreSQLのschemeは`postgresql+psycopg://` |
| WEB_ORIGIN | 許可するWebオリジン。開発URLは`http://127.0.0.1:5173`と揃える |
| SUPABASE_URL / SUPABASE_AUDIENCE | APIでのJWT検証 |
| VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY | ブラウザ用の公開Auth設定 |
| EXECUTION_PROVIDER | disabled / modal |
| MODAL_TOKEN_ID / MODAL_TOKEN_SECRET | Worker用Secret。両方がなければSandboxを無効化 |

下書きは接続が切れても端末へ保持します。完全オフラインでの初回起動や教材読込には対応していません。接続復旧後に下書きを復元できます。

## 状態と制約

詳細な検証結果は[TESTING.md](docs/TESTING.md)、仕様との差分は[IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)を参照してください。SupabaseとModalの実接続、実DBのRLS、OAuthメールの配信は設定待ちです。これらを検証済み・本番公開可能とは扱っていません。pushや公開は実施していません。
