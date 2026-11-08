# セキュリティ境界

## ブラウザ実行

Worker単体は安全性の境界にしません。allow-scriptsのみのsandbox iframe（allow-same-originなし）内にblob Workerを作ります。opaque originからアプリのIndexedDBや認証セッションへアクセスできません。渡すデータはコード・公開入力・公開期待値・公開実行ハーネス・パッケージ名だけです。

postMessageはiframeのWindow、ランダムchannel、run IDを照合します。メッセージサイズを確認し、Pythonのstdout/stderrは各32KBまで、実行は5秒でiframeごと終了します。初期ロードは別の120秒上限です。iframeのCSPはCDN以外へのconnectを禁止します。アプリAPIは異なるOrigin（nullを含む）の変更リクエストを拒否します。

ローカルゲストCookieはHttpOnly・SameSite=Strict、productionではSecureです。WorkerへCookieやBearer tokenを転送しません。ブラウザ採点は改変可能なので、正式習得と分離します。

## サーバー実行

FastAPI内での任意execや、ローカルsubprocess実行アダプターはありません。非公開の期待値はWorkerに残し、Sandboxには入力とコードだけを送ります。Modalはblock_network=True、CPU1、メモリ2GiB、実行30秒、寿命35秒、非root learnerユーザー、秘密・永続volume・GPU・公開portなしで作成します。root所有のイメージと分離し、作業領域は/tmpです。出力は合計64KiBで終了します。finallyでSandboxを破棄します。

この設定は導入SDKのシグネチャで確認しています。実際のModal上でのネットワーク遮断、書込権限、制限、キャンセル、破棄の動作は**認証情報未設定のため未検証**です。実環境の制限検証を完了するまで一般公開しないでください。

## Auth・DB

Supabaseの非対称署名鍵（ES256/RS256）をJWKSから取得し、署名・exp・iat・sub・aud・issを検証します。旧HS256モードへ自動フォールバックしません。JWTの検証に関する単体テストは、署名・期限・issuer・audienceの誤りを拒否します。

RLSと権限剥奪により、所有者の参照だけを許可し、検証済み結果・習熟度・復習・下書きの書込はAPI経由に限定します。Supabaseのservice keyやDB資格情報はVITE_変数へ入れません。

## 公開前の確認

実際のSupabaseでRLSテスト、Google/メールのlinking・既存ユーザー競合、Modalの隔離テストを実行してください。HTTPS、バックアップ、逆プロキシの許可元、監視とレート制限を設定してください。静的配信のCSPがsrcdocの実行用bootstrapやWASMを不意に遮断しないことも確認が必要です。実行iframeを専用の資格情報を持たないオリジンへ配置する構成を本番で推奨します。

実行結果のAST要件は教育上の確認です。高度な悪意のあるPythonがライブラリや観測値を偽装することを完全には防ぎません。ネットワークや秘密の保護を、ASTブラックリストやPython内のモンキーパッチ対策へ依存させません。
