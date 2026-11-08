import { useQuery } from "@tanstack/react-query";
import {
  Check,
  ExternalLink,
  HardDrive,
  Mail,
  Save,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { queries, refreshLearning, supabase, userApi } from "../lib/api";
import { Badge, Button, ErrorBox, Loading, PageTitle } from "../components/ui";
import type { UserSettings } from "../types/domain";
export function Settings() {
  const { data: d, error, isPending } = useQuery(queries.dashboard);
  const [form, setForm] = useState<UserSettings | null>(null),
    [email, setEmail] = useState(""),
    [message, setMessage] = useState(""),
    [err, setErr] = useState<unknown>(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    if (d && !form) setForm(d.settings);
  }, [d]);
  if (isPending || !form)
    return error ? <ErrorBox error={error} /> : <Loading />;
  const current = form;
  function change<K extends keyof UserSettings>(
    key: K,
    value: UserSettings[K],
  ) {
    setForm({ ...current, [key]: value });
    setMessage("");
  }
  async function save() {
    setBusy(true);
    setErr(null);
    try {
      await userApi("/settings", {
        method: "PATCH",
        body: JSON.stringify(current),
      });
      await refreshLearning();
      setMessage("設定を保存しました。");
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  }
  async function google() {
    if (!supabase) return;
    setErr(null);
    const { error } = await supabase.auth.linkIdentity({
      provider: "google",
      options: { redirectTo: location.origin + "/auth/callback" },
    });
    if (error) setErr(error);
  }
  async function linkEmail() {
    if (!supabase || !email) return;
    setBusy(true);
    setErr(null);
    const { error } = await supabase.auth.updateUser(
      { email },
      { emailRedirectTo: location.origin + "/auth/callback" },
    );
    if (error) setErr(error);
    else
      setMessage(
        "確認メールを送信しました。メール内のリンクから認証を完了してください。",
      );
    setBusy(false);
  }
  async function signIn(provider: "google" | "email") {
    if (!supabase) return;
    setBusy(true);
    setErr(null);
    try {
      const result =
        provider === "google"
          ? await supabase.auth.signInWithOAuth({
              provider: "google",
              options: { redirectTo: location.origin + "/auth/callback" },
            })
          : await supabase.auth.signInWithOtp({
              email,
              options: {
                shouldCreateUser: false,
                emailRedirectTo: location.origin + "/auth/callback",
              },
            });
      if (result.error) throw result.error;
      if (provider === "email")
        setMessage(
          "ログイン用メールを送信しました。現在のゲスト履歴は別IDとして保持されます。",
        );
    } catch (error) {
      setErr(error);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="MAKE IT YOURS"
        title="学習環境を整える"
        description="自分のペースと、書きやすいエディタに。"
      />
      {!!err && <ErrorBox error={err} />}
      <div className="settings-layout">
        <section className="panel settings-panel">
          <div className="settings-section">
            <h2>プロフィール</h2>
            <p>学習画面に表示する名前を設定します。</p>
            <label>
              表示名
              <input
                maxLength={60}
                value={form.display_name}
                onChange={(e) => change("display_name", e.target.value)}
              />
            </label>
          </div>
          <div className="settings-section">
            <h2>外観とエディタ</h2>
            <div className="settings-field-grid">
              <label>
                テーマ
                <select
                  aria-label="テーマ"
                  value={form.theme}
                  onChange={(e) =>
                    change("theme", e.target.value as UserSettings["theme"])
                  }
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="system">システムに合わせる</option>
                </select>
              </label>
              <label>
                フォントサイズ
                <select
                  aria-label="フォントサイズ"
                  value={form.font_size}
                  onChange={(e) => change("font_size", Number(e.target.value))}
                >
                  {[12, 13, 14, 15, 16, 18, 20, 22, 24].map((n) => (
                    <option key={n} value={n}>
                      {n}px
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <pre
              style={{ fontSize: form.font_size }}
              className="settings-preview"
            >
              <span className="code-purple">def</span> learn_by_doing():
              <br />
              {"    "}
              <span className="code-purple">return</span>{" "}
              <span className="code-green">"Write. Run. Understand."</span>
            </pre>
          </div>
          <div className="settings-section">
            <h2>学習目標と時刻</h2>
            <div className="settings-field-grid">
              <label>
                1日の目標問題数
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={form.daily_goal}
                  onChange={(e) => change("daily_goal", Number(e.target.value))}
                />
              </label>
              <label>
                タイムゾーン
                <select
                  value={form.timezone}
                  onChange={(e) => change("timezone", e.target.value)}
                >
                  {[
                    ...new Set([
                      form.timezone,
                      "Asia/Tokyo",
                      "UTC",
                      "America/New_York",
                      "America/Los_Angeles",
                      "Europe/London",
                      "Asia/Singapore",
                    ]),
                  ].map((tz) => (
                    <option key={tz}>{tz}</option>
                  ))}
                </select>
              </label>
            </div>
          </div>
          <div className="settings-save">
            <span role="status">
              {message && (
                <>
                  <Check size={16} />
                  {message}
                </>
              )}
            </span>
            <Button
              disabled={
                busy ||
                !form.display_name.trim() ||
                form.daily_goal < 1 ||
                form.daily_goal > 100
              }
              onClick={save}
            >
              <Save size={16} />
              変更を保存
            </Button>
          </div>
        </section>
        <aside>
          <section className="panel account-panel">
            <ShieldCheck size={25} />
            <h2>アカウント</h2>
            <Badge color={supabase ? "green" : "gray"}>
              {supabase ? "Supabase Auth" : "ローカルゲスト"}
            </Badge>
            <p>
              {supabase
                ? "ゲストの学習履歴を残したまま、ログイン方法を追加できます。"
                : "この端末のゲストIDでAPIのSQLiteに保存しています。クラウド認証は未設定です。"}
            </p>
            <Button variant="secondary" disabled={!supabase} onClick={google}>
              <GoogleIcon />
              Googleと連携
              <ExternalLink size={14} />
            </Button>
            <label>
              メールアドレス
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={!supabase}
              />
            </label>
            <Button
              variant="secondary"
              disabled={!supabase || !email.includes("@") || busy}
              onClick={linkEmail}
            >
              <Mail size={16} />
              確認メールを送信
            </Button>
            <small>
              既存の別アカウントへの履歴自動統合は行いません。連携が競合する場合、履歴は保持されます。
            </small>
            <details className="account-signin">
              <summary>既存アカウントでログイン</summary>
              <p>
                このゲストIDとは別にログインします。履歴の自動統合はありません。
              </p>
              <Button
                variant="secondary"
                disabled={!supabase || busy}
                onClick={() => signIn("google")}
              >
                Googleでログイン
              </Button>
              <Button
                variant="ghost"
                disabled={!supabase || !email.includes("@") || busy}
                onClick={() => signIn("email")}
              >
                入力したメールでログイン
              </Button>
            </details>
          </section>
          <section className="panel storage-note">
            <HardDrive size={19} />
            <div>
              <h3>コードを、消さないために。</h3>
              <p>
                下書きは端末のIndexedDBへ自動保存し、APIにも同期します。競合時はローカルのコードを保持します。
              </p>
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}
function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 20 20" aria-hidden="true">
      <path
        fill="currentColor"
        d="M19 10.2c0-.6-.1-1.3-.2-1.9H10v3.6h5a4.3 4.3 0 0 1-1.9 2.8v2.4h3C18 15.5 19 13.1 19 10.2Z"
      />
      <path
        fill="currentColor"
        opacity=".7"
        d="M10 19c2.6 0 4.7-.9 6.2-2.4l-3-2.4c-.8.5-1.8.8-3.2.8-2.5 0-4.6-1.7-5.3-4H1.5v2.5C3 16.8 6.2 19 10 19ZM4.7 9c0-.6.1-1.2.3-1.7V4.8H1.5a9 9 0 0 0 0 8.7l3.2-2.5A6 6 0 0 1 4.7 9ZM10 4c1.4 0 2.6.5 3.6 1.4l2.7-2.7A9 9 0 0 0 1.5 4.8L5 7.3A5.3 5.3 0 0 1 10 4Z"
      />
    </svg>
  );
}
export function AuthCallback() {
  const navigate = useNavigate(),
    [error, setError] = useState<unknown>(null);
  useEffect(() => {
    (async () => {
      if (!supabase) throw new Error("Supabase Authが未設定です。");
      const code = new URLSearchParams(location.search).get("code");
      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) throw error;
      }
      await refreshLearning();
      navigate("/home", { replace: true });
    })().catch(setError);
  }, []);
  return error ? <ErrorBox error={error} /> : <Loading />;
}
