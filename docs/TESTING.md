# 検証手順と実行記録

2026-11-03、Windows、Node 24、CPython 3.13で実行しています。成果物は`artifacts/`、Playwrightの失敗時詳細は`test-results/`です。これらはローカル検証の生成物としてGitから除外しています。

| コマンド | 確認対象 |
|---|---|
| `npm run typecheck` | strict TypeScript |
| `npm run lint` | ESLint / React Hooks |
| `npm run test` | Vitest + React Testing Library。数値比較・dtype・shape・下書き復元・競合・UI |
| `npm run build` | Vite本番ビルド。MonacoはPythonに絞って遅延ロード |
| `uv run --project apps/api ruff check --config apps/api/pyproject.toml apps/api content scripts` | Python lint |
| `uv run --project apps/api python -m pytest apps/api/tests -q` | FastAPI・SQLite・署名・採点・進行・全活動・読解実行 |
| `uv run --project apps/api python scripts/validate_content.py` | 180問、30概念、形式配分、seed再現性、模範解答、誤答、バグ検出 |
| `npm run test:e2e` | 実際のChromiumで編集・実行・提出・エラー・保存・復元・再開・mobile・theme |
| `npm run test:browser-content` | 120問の模範解答を本番と同じPyodide実行経路で検証 |
| `uv run --project apps/api python scripts/check_security.py` | 公開教材に秘密がないこと、API内exec禁止、Sandbox設定 |
| `npm audit` | npm依存監査 |

## 実行済みの検証

- Backend: **46 passed / 2 skipped**。署名・期限・issuer・audience拒否、ユーザー間の404、revision競合、二重提出、transaction rollback、ヒントと解答閲覧、暫定と正式の段階ゲートを含みます。
- Frontend unit: **8 passed**。
- Native content: **180/180問**。2つのseedで**1,440ケース合格**、代表誤答360件を拒否。30のバグ修正用初期コードも両seedで不合格を確認しています。
- 読解: NumPy 105行/3ファイル、scikit-learn 135行/4ファイル、PyTorch 219行/5ファイル。各CLIとPyTorch推論がpytestで実行できています。
- E2E: 最終一括実行で**6 passed / 1 skipped**。skipは別コマンドで実施する全件Pyodideテストです。
- Pyodide全件: **120/120問、480/480ケース合格**。seed 42の公開・非公開ケースを実際のブラウザ実行経路で検証しました。12分で完了しました。nativeの検証はseed 42/99の両方です。
- `npm audit`: 脆弱性0件。DOMPurifyとminimatchの修正版overrideを固定し、型チェック・ビルド・lintで互換性を確認しています。

実装途中のPyodide全件検証で、初回importをコード実行時間へ含める問題を検出しました。パッケージのimportを初期化フェーズへ移し、学習者のコードに対する5秒制限を維持しています。Workerは完了・中止・エラーで明示的に終了します。

## 外部環境が必要なテスト

Modal実接続とSupabase実DB RLSは資格情報がないため明示的にskipします。モック結果を実サービスの検証として数えません。通常テスト内で作成するcompleted jobは段階ゲートの検証専用fixtureです。

- `RLS_TEST_DATABASE_URL`: migration適用済みの専用SupabaseテストDB。SET LOCAL ROLE authenticatedで行分離と更新拒否を確認しrollbackします。
- `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` / `RUN_LIVE_MODAL_TESTS=1`: 課金を伴う可能性のあるSandbox smoke testを明示的に許可します。
- Google OAuth、メールの配信とlinking競合は実際のテストアカウントで手動確認が必要です。

## 手動確認

1. 新規ブラウザで学習を始め、履歴が0件から増えること。
2. Ctrl+Enter / Ctrl+Shift+Enter / Alt+H / Alt+N、MacのCommand、IME変換中の抑止。
3. 分割幅と結果高をドラッグ／キーボードで変え、集中モードへ切り替える。
4. オフライン、DB通信失敗、2タブ同時編集でもコードが残ること。
5. 390px・768px・1440pxで操作でき、ライトテーマと文字サイズが保存されること。
6. Sandboxのネットワーク、メモリ、CPU、ファイル権限、timeout、cancelと自動破棄。

GitHub Actionsはlint・typecheck・build・unit・integration・native content・OpenAPI差分・セキュリティ不変条件・E2E・npm auditを実行します。ワークフロー自体のGitHub上での実行はpushしていないため未検証です。

## 最終記録

実際に使用したWindowsコマンドと最終結果:

```text
npm run lint                                      成功
npm run typecheck                                 成功
npm run test                                      8 passed
npm run build                                     成功
apps/api/.venv/Scripts/ruff.exe check --config apps/api/pyproject.toml apps/api content scripts
                                                  All checks passed
apps/api/.venv/Scripts/python.exe -m pytest apps/api/tests -q
                                                  46 passed / 2 skipped
apps/api/.venv/Scripts/python.exe scripts/validate_content.py
                                                  180問 / 1,440 cases / failures 0
apps/api/.venv/Scripts/python.exe scripts/check_security.py
                                                  passed
npm run test:e2e                                  6 passed / 1 skipped (1.1分)
npm run test:browser-content                      1 passed、120問480ケース (12.1分)
npm audit                                        0 vulnerabilities
```

API出力スキーマとOpenAPI型生成も確認しています。pytestにStarlette/AnyIO由来のdeprecation warningが1件あります。Console errorを監視する主要E2Eでは重大なpageerrorはありません。

Pyodideは配布版のライブラリセットを使うため、native検証環境とパッケージの版が一致するとは限りません。ブラウザ対象は上記の実行経路で値まで比較しています。各RunでWorkerを作り直すため、ファイル取得がキャッシュされてもPythonやライブラリの初期化時間は発生します。
