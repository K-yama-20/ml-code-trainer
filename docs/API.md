# API

共通prefixは`/api/v1`です。起動時の`/docs`と`apps/api/openapi.json`がエンドポイントと入力型の基準です。

- 教材: modules / concepts / problems / deep-dives / reading-projects
- セッション: sessions作成・current・個別取得・items取得・pause/resume/complete
- 実行: executions作成・状態取得・cancel
- 提出: submissions作成・ID取得・by-request取得
- 補助: session-itemsのhints/solution reveal、drafts GET/PUT
- 学習: dashboard / progress/summary / progress/concepts / reviews/due / history
- 設定: settings GET/PATCH、auth/guest、auth/me
- 読解とDeep Dive: activities/{id}/answers

ユーザーIDを本文から受け取るAPIはありません。Supabase JWTまたは開発用guest Cookieから決定します。Pydanticは未知の入力フィールドを拒否し、コードの上限は16KiB、通常のJSON入力は100KBまでです。

エラーは`{"error":{"code":"...","message":"...","request_id":"..."}}`です。レスポンスには`X-Request-ID`と`Cache-Control: no-store`を付けます。historyはlimit/offsetで最大100行です。副作用のある操作はTanStack Queryやfetchで無条件に再送しません。

実行・提出・ゲスト作成・セッション作成をDBベースの分単位カウンターで制限します。実行はユーザー10件/分、IP30件/分、提出30件/分が初期値です。IPは直接の接続元を利用します。逆プロキシを置く場合は信頼するプロキシだけから転送ヘッダーを受け入れるようUvicornを設定し、エッジ側にも制限を置いてください。

正式提出には、所有者・item・コードハッシュ・mode=submitが一致するcompleted jobが必要です。クライアントのacceptedやverification_levelを送っても正式採点にはなりません。

型の再生成:

```powershell
uv run --project apps/api python scripts/export_openapi.py
npm run api:types
```

生成物は`apps/web/src/types/api.d.ts`です。UIの読みやすいドメイン型は`types/domain.ts`で管理し、API integration testsで契約を検証します。
