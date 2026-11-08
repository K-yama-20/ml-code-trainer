# 外部サービス設定とデプロイ

この作業ではpush・公開・有料実行を行っていません。以下は運用者が設定を完了して検証するための手順です。

## Supabase / PostgreSQL

1. Supabaseプロジェクトを作り、DBを用意します。専用のテスト環境を先に設定してください。
2. Supabase CLIでプロジェクトをlinkし、`supabase db push`でリポジトリのmigrationを適用します。SQL Editorで同じmigrationを適用する方法でも構いません。
3. サーバーのDATABASE_URLにPostgreSQL接続を設定します。例のschemeは`postgresql+psycopg://`です。接続パスワードはサーバーのSecretに保存します。
4. `SUPABASE_URL`、`SUPABASE_AUDIENCE=authenticated`、`APP_ENV=production`、`WEB_ORIGIN=https://実際のアプリのオリジン`をサーバーへ設定します。
5. Webビルドには`VITE_SUPABASE_URL`と公開用anon/publishable keyを`VITE_SUPABASE_ANON_KEY`として設定します。secret/service role keyは使用しません。
6. 新しい非対称JWT signing key（ES256またはRS256）を有効にします。APIはJWKSを使います。
7. Anonymous sign-insとManual Identity Linkingを有効にします。匿名アカウントはauthenticatedロールです。
8. Auth URL Configurationに本番サイトと`https://アプリ/auth/callback`を許可します。開発時は`http://127.0.0.1:5173/auth/callback`も追加します。
9. `uv run --project apps/api python scripts/seed_content.py`で教材を同期します。

匿名認証への公開アクセスにはSupabase側の濫用対策・CAPTCHAも運用方針に合わせて設定します。アプリは登録を強制せず、初回に匿名IDを作ります。

## Googleとメール

Google CloudでOAuth Webクライアントを作成し、Supabase側のcallback URLをGoogleの許可済みredirect URIへ登録します。Googleのclient ID/secretはSupabase管理画面にだけ保存し、Google providerを有効にします。

メールproviderと確認メールを有効にし、実運用ではSMTP配信を設定します。アプリの「確認メールを送信」は匿名ユーザーのemailをupdateUserして確認させる昇格フローです。GoogleはlinkIdentityで同じIDを保ちます。すでに別IDへ同じidentityが紐付く場合の自動履歴統合は実装していません。

## Modal

サーバー/WorkerのSecretに`MODAL_TOKEN_ID`、`MODAL_TOKEN_SECRET`を設定し、`EXECUTION_PROVIDER=modal`を有効にします。トークンをSandboxのenvやSecret bindingsへ入れないでください。

APIとは別のプロセスで実行します。

```powershell
uv run --project apps/api python -m apps.api.app.worker
```

最初の実行で`ml-code-trainer` Appとイメージが作られます。CPU用torchを含むイメージのビルドは時間がかかります。WorkerがAPIと同じDB・同じ教材バージョンを参照している必要があります。Workerの多重起動はCAS claimで対応しますが、最初は1プロセスで検証してください。

隔離の実検証は`RUN_LIVE_MODAL_TESTS=1`を設定して該当pytestを実行します。課金が発生し得るため、CIはデフォルトで実行しません。

## Web / APIの配信

`npm ci && npm run build`で`apps/web/dist`を生成します。SPAルートはindex.htmlへフォールバックし、`/api/*`をFastAPIへ転送します。FastAPIとWorkerはPythonの本番用プロセスマネージャーで別々に起動し、HTTPSの同一オリジンから利用します。

Webサーバーは`apps/web/dist`だけを配信します。リポジトリルートを静的公開するとprivate教材や設定が露出するため禁止です。教材用ディレクトリはAPI/Workerの配布物にのみ含めます。

設定反映後、ゲスト→実行→提出→保存→リロード、Google/メール昇格、別ユーザー参照拒否、独立問題の正式採点、Sandboxキャンセル・timeout・network遮断、スマートフォン表示を確認します。実接続検証が済むまでは開発版として扱ってください。
