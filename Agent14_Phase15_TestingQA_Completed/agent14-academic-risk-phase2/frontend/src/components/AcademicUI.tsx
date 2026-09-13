import type { ReactNode } from "react";

export type AcademicStatus = "LOW" | "MODERATE" | "HIGH" | "CRITICAL" | "NEUTRAL";

const STATUS_STYLES: Record<AcademicStatus, string> = {
  LOW: "border-emerald-200 bg-emerald-50 text-emerald-700",
  MODERATE: "border-amber-200 bg-amber-50 text-amber-800",
  HIGH: "border-orange-200 bg-orange-50 text-orange-800",
  CRITICAL: "border-red-200 bg-red-50 text-red-800",
  NEUTRAL: "border-slate-200 bg-slate-50 text-slate-600",
};

export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="ui-section-heading">
      <div className="min-w-0">
        <p className="ui-eyebrow">{eyebrow}</p>
        <h2 className="ui-section-title">{title}</h2>
        {description ? <p className="ui-section-description">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function StatusChip({ level, children }: { level: AcademicStatus | string; children?: ReactNode }) {
  const normalized = String(level).toUpperCase() as AcademicStatus;
  const safe = normalized in STATUS_STYLES ? normalized : "NEUTRAL";
  return <span className={`ui-status-chip ${STATUS_STYLES[safe]}`}>{children ?? normalized}</span>;
}

export function ActionButton({
  children,
  variant = "primary",
  type = "button",
  disabled,
  onClick,
  className = "",
  ariaLabel,
}: {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  ariaLabel?: string;
}) {
  const styles = {
    primary: "ui-button ui-button-primary",
    secondary: "ui-button ui-button-secondary",
    ghost: "ui-button ui-button-ghost",
    danger: "ui-button ui-button-danger",
  }[variant];
  return (
    <button type={type} disabled={disabled} onClick={onClick} aria-label={ariaLabel} className={`${styles} ${className}`}>
      {children}
    </button>
  );
}

export function Icon({ name }: { name: "students" | "critical" | "attention" | "alerts" | "back" | "open" | "filter" }) {
  const common = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, className: "h-5 w-5" };
  switch (name) {
    case "students":
      return <svg {...common} aria-hidden="true"><circle cx="9" cy="8" r="3" /><path d="M3.5 19c.3-3 2.1-5 5.5-5s5.2 2 5.5 5" /><path d="M15 6.5a2.5 2.5 0 1 1 0 5" /><path d="M16 14c2.8.1 4.4 1.8 4.5 4" /></svg>;
    case "critical":
      return <svg {...common} aria-hidden="true"><path d="M12 3 2.8 20h18.4L12 3Z" /><path d="M12 8.5v5.2" /><circle cx="12" cy="17.2" r=".7" fill="currentColor" stroke="none" /></svg>;
    case "attention":
      return <svg {...common} aria-hidden="true"><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="3.2" /><path d="M12 3.5v4" /><path d="M20.5 12h-4" /></svg>;
    case "alerts":
      return <svg {...common} aria-hidden="true"><path d="M18 9a6 6 0 0 0-12 0c0 6-2.5 6-2.5 7.5h15C18.5 15 18 15 18 9Z" /><path d="M10 20h4" /></svg>;
    case "back":
      return <svg {...common} aria-hidden="true"><path d="M14.5 6 8.5 12l6 6" /></svg>;
    case "open":
      return <svg {...common} aria-hidden="true"><path d="M9 5h10v10" /><path d="m19 5-9 9" /><path d="M19 13v5H5V5h5" /></svg>;
    case "filter":
      return <svg {...common} aria-hidden="true"><path d="M4 6h16" /><path d="M7 12h10" /><path d="M10 18h4" /></svg>;
  }
  return null;
}

export function MetricCard({
  label,
  value,
  detail,
  icon,
  tone = "neutral",
  loading = false,
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: "students" | "critical" | "attention" | "alerts";
  tone?: "neutral" | "critical" | "attention" | "brand";
  loading?: boolean;
}) {
  const iconTone = tone === "critical" ? "text-red-700 bg-red-50 border-red-100" : tone === "attention" ? "text-orange-700 bg-orange-50 border-orange-100" : tone === "brand" ? "text-brand-700 bg-brand-50 border-brand-100" : "text-brand-700 bg-[#edf4ff] border-[#d7e6fb]";
  return (
    <article className="ui-metric-card">
      <div className={`ui-metric-icon ${iconTone}`}><Icon name={icon} /></div>
      <div className="min-w-0">
        <p className="ui-metric-label">{label}</p>
        {loading ? (
          <div className="mt-2 h-9 w-16 animate-pulse rounded-lg bg-slate-100" aria-label={`Loading ${label}`} />
        ) : (
          <p className="ui-metric-value">{value}</p>
        )}
        <p className="ui-metric-detail">{detail}</p>
      </div>
    </article>
  );
}

export function KeyValue({ label, value }: { label: string; value: ReactNode }) {
  return <div className="ui-key-value"><p className="ui-key-label">{label}</p><p className="ui-key-value-text">{value}</p></div>;
}
