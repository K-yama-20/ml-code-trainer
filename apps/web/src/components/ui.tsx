import {
  ArrowUpRight,
  ChevronRight,
  LoaderCircle,
  Terminal,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import type { ButtonHTMLAttributes, ReactNode } from "react";
export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
}) {
  return (
    <button className={`btn ${variant} ${className}`} {...props}>
      {children}
    </button>
  );
}
export function Badge({
  children,
  color = "blue",
}: {
  children: ReactNode;
  color?: string;
}) {
  return <span className={`badge ${color}`}>{children}</span>;
}
export function ProgressBar({
  value,
  color,
}: {
  value: number;
  color?: string;
}) {
  return (
    <div className="progress-track">
      <div
        style={{
          width: `${Math.min(100, Math.max(0, value))}%`,
          background: color,
        }}
      />
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading">
      <LoaderCircle className="spin" size={24} />
      <span>読み込んでいます…</span>
    </div>
  );
}
export function ErrorBox({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  return (
    <div className="error-box" role="alert">
      <strong>処理を完了できませんでした</strong>
      <p>{error instanceof Error ? error.message : String(error)}</p>
      {retry && (
        <Button variant="secondary" onClick={retry}>
          再試行
        </Button>
      )}
    </div>
  );
}
export function Empty({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <Terminal size={30} />
      <h3>{title}</h3>
      <p>{description}</p>
      {children}
    </div>
  );
}
export function PageTitle({
  eyebrow,
  title,
  description,
  children,
  level = 1,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  children?: ReactNode;
  level?: 1 | 2;
}) {
  const Heading = level === 1 ? "h1" : "h2";
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <Heading>{title}</Heading>
        {description && <p>{description}</p>}
      </div>
      {children}
    </div>
  );
}
export function SectionTitle({
  title,
  to,
  label = "すべて見る",
}: {
  title: string;
  to?: string;
  label?: string;
}) {
  return (
    <div className="section-title">
      <h2>{title}</h2>
      {to && (
        <Link to={to}>
          {label}
          <ChevronRight size={15} />
        </Link>
      )}
    </div>
  );
}
export function TextLink({
  to,
  children,
}: {
  to: string;
  children: ReactNode;
}) {
  return (
    <Link className="text-link" to={to}>
      {children}
      <ArrowUpRight size={16} />
    </Link>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <header>
          <h2>{title}</h2>
          <button aria-label="閉じる" className="icon-btn" onClick={onClose}>
            <X />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
export const stageLabels = {
  guided: "Guided",
  partial: "Partial",
  independent: "Independent",
};
export const typeLabels: Record<string, string> = {
  completion: "穴埋め・部分記述",
  prediction: "出力・shape予測",
  implementation: "自力実装",
  bugfix: "バグ修正",
};
