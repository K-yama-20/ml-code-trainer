# データベース

ローカルはSQLAlchemyでSQLiteスキーマを初期化します。本番は`supabase/migrations/202611030001_initial.sql`を適用し、自動create_allを無効にします。TIMESTAMPTZはUTC、表示・連続学習日の計算はユーザー設定のIANA timezoneを使います。

| 領域 | テーブル |
|---|---|
| 公開教材 | curriculum_modules / concepts / concept_prerequisites / problem_families / problem_versions / deep_dive_tasks / reading_projects / reading_questions |
| 学習者 | profiles / user_settings |
| セッション・保存 | study_sessions / session_items / problem_drafts |
| 学習履歴・集計 | submission_attempts / user_problem_progress / user_concept_progress / review_schedules / activity_progress |
| 実行・利用量 | execution_jobs / system_usage_daily |
| 非公開 | private.grader_test_sets / private.activity_answers |

公開教材はanon/authenticatedにSELECTだけを許可します。ユーザーテーブルはauthenticatedに`auth.uid()`と一致する行のSELECTだけを許可します。更新はAPIで検証し、trusted DB接続で行います。認証済み匿名ユーザーにも同じRLSが適用されます。クライアントにverified progressやjob.resultの更新権限はありません。

private schemaはPUBLIC/anon/authenticatedからUSAGEとテーブル権限を剥奪し、RLSを有効にします。service role keyをブラウザに渡す構成ではありません。API/Worker用DB認証情報はサーバーにのみ設定します。

提出は(user_id,client_request_id)がuniqueです。同じIDの再送は同じ結果を返し、コードやitemが異なれば409です。履歴追加、習熟度更新、復習更新は同じDB transactionで行います。PostgreSQLではユーザー行をFOR UPDATEして集計の競合を直列化します。下書きは(user_id,item_id,revision)の条件付きUPDATEです。

active jobはユーザー単位のpartial unique index、ジョブclaimは条件付きUPDATEで保護します。claim・履歴日付・セッション再開・復習期限にindexを用意しています。

`scripts/seed_content.py`は公開データと非公開データを分けて同期します。公開済みバージョンを上書きしようとすると失敗します。旧バージョンを消す処理やゲスト履歴を別アカウントへ上書きする処理はありません。

実DB RLSテストは`RLS_TEST_DATABASE_URL`で専用SupabaseテストDBを指定した場合だけ動きます。テスト用の行はtransaction rollbackで破棄します。本番のURLを指定しないでください。
