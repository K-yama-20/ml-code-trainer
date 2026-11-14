import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BookOpen,
  Boxes,
  ChevronRight,
  Code2,
  Flame,
  GraduationCap,
  History,
  House,
  Menu,
  Settings2,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { problemCount, queries } from "../lib/api";
import { useUI } from "../lib/store";
import { ProgressBar } from "../components/ui";
import { WorkspaceDrawer } from "./WorkspaceDrawer";
const links = [
  { to: "/home", label: "ホーム", icon: House },
  { to: "/curriculum", label: "カリキュラム", icon: Boxes },
  { to: "/drill", label: "Drill", icon: Code2 },
  { to: "/reading", label: "Code Reading", icon: BookOpen },
  { to: "/analytics", label: "学習分析", icon: Activity },
  { to: "/history", label: "解答履歴", icon: History },
];
export function Layout() {
  const { data } = useQuery(queries.dashboard);
  const { data: concepts } = useQuery(queries.concepts);
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const { focus } = useUI();
  const saveDrillDraft = useRef<(() => Promise<void>) | null>(null);
  const drill = pathname.startsWith("/drill/s/");
  useEffect(() => {
    setOpen(false);
  }, [pathname]);
  const sidebar = (
    <aside className={`sidebar ${!drill && open ? "open" : ""}`}>
      <NavLink to="/home" className="brand">
        <span className="brand-mark">
          <Code2 size={21} />
        </span>
        <span>
          ML Code<span className="brand-light">Trainer</span>
        </span>
      </NavLink>
      <div className="sidebar-label">WORKSPACE</div>
      <nav>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            to={to}
            key={to}
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            <Icon size={18} />
            <span>{label}</span>
            {to === "/drill" && concepts && (
              <span className="nav-pill">{problemCount(concepts)}</span>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-note">
        <span className="note-icon">
          <Sparkles size={17} />
        </span>
        <strong>読む力は、書くことから。</strong>
        <p>小さな実装を、毎日の習慣に。</p>
        <NavLink to="/curriculum">
          学習ロードマップ
          <ChevronRight size={14} />
        </NavLink>
      </div>
      <div className="sidebar-bottom">
        <NavLink className="nav-link" to="/settings">
          <Settings2 size={18} />
          設定
        </NavLink>
        <div className="profile">
          <div className="avatar">
            {(data?.user.display_name ?? "L").slice(0, 1).toUpperCase()}
          </div>
          <div>
            <strong>{data?.user.display_name ?? "Learner"}</strong>
            <span>
              {data?.auth_mode === "supabase"
                ? "学習アカウント"
                : "ローカルゲスト"}
            </span>
          </div>
          <span className="status-dot" />
        </div>
      </div>
    </aside>
  );
  return (
    <div
      className={`app-shell ${drill ? "drill-shell" : ""} ${drill && focus ? "focused" : ""}`}
    >
      {!drill && open && (
        <button
          className="nav-scrim"
          aria-label="ナビゲーションを閉じる"
          onClick={() => setOpen(false)}
        />
      )}
      {!drill && sidebar}
      <div className="app-body">
        <header className="topbar">
          <div className="breadcrumbs">
            {drill ? (
              <WorkspaceDrawer
                key={pathname}
                saveDraft={() => saveDrillDraft.current?.()}
              >
                {sidebar}
              </WorkspaceDrawer>
            ) : (
              <>
                <button
                  className="icon-btn menu-toggle"
                  aria-label="メニューを開く"
                  onClick={() => setOpen(!open)}
                >
                  {open ? <X size={19} /> : <Menu size={19} />}
                </button>
                <GraduationCap size={17} />
              </>
            )}
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>
              {links.find((l) => pathname.startsWith(l.to))?.label ??
                (pathname.startsWith("/deep-dive")
                  ? "Deep Dive"
                  : "概念を学ぶ")}
            </strong>
          </div>
          <div className="topbar-actions">
            <span className="streak-small">
              <Flame size={16} />
              {data?.streak ?? 0}
              <span>日連続</span>
            </span>
            <span className="top-divider" />
            <NavLink to="/settings" className="small-avatar">
              {(data?.user.display_name ?? "L").slice(0, 1).toUpperCase()}
            </NavLink>
          </div>
        </header>
        {!drill && (
          <div className="mobile-goal">
            <Target size={15} />
            今日の目標 {data?.today_count ?? 0}/
            {data?.settings.daily_goal ?? 20}問
            <ProgressBar
              value={
                ((data?.today_count ?? 0) / (data?.settings.daily_goal ?? 20)) *
                100
              }
            />
          </div>
        )}
        <main className={drill ? "drill-main" : "page-main"}>
          <Outlet context={saveDrillDraft} />
        </main>
        <footer className="app-footer">
          <span>ML CODE TRAINER</span>
          <span>Write. Run. Understand.</span>
          <span className="footer-status">
            <span className="status-dot" />
            {data?.auth_mode === "supabase" ? "クラウド保存" : "ローカルDB保存"}
          </span>
        </footer>
      </div>
    </div>
  );
}
