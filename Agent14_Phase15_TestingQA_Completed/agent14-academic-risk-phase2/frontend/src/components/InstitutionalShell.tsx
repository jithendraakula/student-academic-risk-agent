import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

interface NotificationItem {
  id: string;
  title?: string;
  message?: string;
  is_read?: boolean;
  created_at?: string;
  category?: "action_required" | "follow_up" | "escalation" | "information";
  student_id?: string;
  student_name?: string;
  risk_label?: string;
  risk_level?: string;
  priority_score?: number;
  alert_status?: string;
  action_required?: boolean;
  roll_number?: string | null;
  section?: string | null;
  department?: string | null;
  recommended_action?: string | null;
  evidence?: string | null;
}

interface NotificationResponse {
  items: NotificationItem[];
  unread?: number;
  total?: number;
  action_required?: number;
  follow_up?: number;
  escalation?: number;
}

interface Props {
  children: ReactNode;
  eyebrow: string;
  title: string;
  subtitle?: string;
}

const NAV: Record<string, Array<{ label: string; to: string; icon: string }>> = {
  mentor: [{ label: "Mentor dashboard", to: "/mentor", icon: "▦" }],
  hod: [{ label: "Department dashboard", to: "/hod", icon: "▦" }],
  dean: [{ label: "Institution dashboard", to: "/dean", icon: "▦" }],
  admin: [{ label: "Administration", to: "/admin", icon: "⚙" }],
};

const ROLE_LABEL: Record<string, string> = {
  mentor: "Mentor",
  hod: "Head of Department",
  dean: "Dean",
  admin: "System Administrator",
};

function timeAgo(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const mins = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

const CATEGORY_META = {
  action_required: { label: "Action required", className: "bg-red-50 text-red-700 border-red-100" },
  follow_up: { label: "Follow-up", className: "bg-amber-50 text-amber-700 border-amber-100" },
  escalation: { label: "Escalation", className: "bg-blue-50 text-blue-700 border-blue-100" },
  information: { label: "Information", className: "bg-slate-50 text-slate-600 border-slate-100" },
} as const;

function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [summary, setSummary] = useState({ action_required: 0, follow_up: 0, escalation: 0, total: 0 });
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<"all" | "unread" | "action_required" | "follow_up">("all");

  async function loadNotifications() {
    setLoading(true);
    try {
      const response = await api.get<NotificationResponse>("/notifications", { params: { limit: 12, unread_only: filter === "unread" } });
      setItems(response.data.items ?? []);
      setUnread(response.data.unread ?? (response.data.items ?? []).filter((item) => !item.is_read).length);
      setSummary({
        action_required: response.data.action_required ?? 0,
        follow_up: response.data.follow_up ?? 0,
        escalation: response.data.escalation ?? 0,
        total: response.data.total ?? 0,
      });
    } catch {
      // Notification delivery is additive to the main workspace; keep the shell usable.
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadNotifications(); }, [filter]);

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  async function markAllRead() {
    if (!unread) return;
    try {
      await api.post("/notifications/read-all");
      setItems((current) => current.map((item) => ({ ...item, is_read: true })));
      setUnread(0);
    } catch {
      // Keep the action center usable when the service is temporarily unavailable.
    }
  }

  async function markRead(id: string) {
    try {
      await api.patch(`/notifications/${id}/read`);
      setItems((current) => current.map((item) => item.id === id ? { ...item, is_read: true } : item));
      setUnread((count) => Math.max(0, count - 1));
    } catch {
      // Keep the notification center usable when the service is temporarily unavailable.
    }
  }

  async function openNotification(item: NotificationItem) {
    if (!item.is_read) await markRead(item.id);
    setOpen(false);
    if (item.student_id) navigate(`/mentor/student/${item.student_id}`);
  }

  const visibleItems = useMemo(() => items.filter((item) => {
    if (filter === "all" || filter === "unread") return true;
    return item.category === filter;
  }), [items, filter]);

  const panel = open ? (
    <>
      <div className="fixed inset-0 z-[80] bg-slate-900/10 sm:bg-transparent" aria-hidden="true" onClick={() => setOpen(false)} />
      <div id="academic-action-center" role="dialog" aria-modal="true" aria-label="Academic action center" className="fixed left-3 right-3 top-[76px] z-[90] flex max-h-[calc(100vh-92px)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/15 sm:left-auto sm:right-5 sm:w-[min(460px,calc(100vw-40px))]">
        <div className="shrink-0 border-b border-slate-100 px-4 pb-3 pt-4 md:px-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[11px] font-extrabold uppercase tracking-[0.12em] text-brand-700">Action center</p>
              <h2 className="mt-1 text-base font-extrabold text-[#18345f]">Academic actions and follow-ups</h2>
              
            </div>
            <button type="button" onClick={() => setOpen(false)} className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50" aria-label="Close academic action center">×</button>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            <div className="rounded-lg bg-[#f5f9ff] px-2.5 py-2"><p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">Action</p><p className="mt-1 text-sm font-extrabold text-red-700">{summary.action_required}</p></div>
            <div className="rounded-lg bg-[#fffaf0] px-2.5 py-2"><p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">Follow-up</p><p className="mt-1 text-sm font-extrabold text-amber-700">{summary.follow_up}</p></div>
            <div className="rounded-lg bg-[#f5f9ff] px-2.5 py-2"><p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">Unread</p><p className="mt-1 text-sm font-extrabold text-brand-700">{unread}</p></div>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-1.5" role="tablist" aria-label="Notification filters">
            {([["all", `All${summary.total ? ` · ${summary.total}` : ""}`], ["unread", `Unread${unread ? ` · ${unread}` : ""}`], ["action_required", `Action required${summary.action_required ? ` · ${summary.action_required}` : ""}`], ["follow_up", `Follow-up${summary.follow_up ? ` · ${summary.follow_up}` : ""}`]] as const).map(([value, label]) => (
              <button key={value} type="button" role="tab" aria-selected={filter === value} onClick={() => setFilter(value)} className={`rounded-lg border px-2.5 py-1.5 text-[10px] font-bold transition ${filter === value ? "border-brand-200 bg-brand-50 text-brand-700" : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"}`}>
                {label}
              </button>
            ))}
            {unread > 0 ? <button type="button" onClick={() => void markAllRead()} className="ml-auto text-[10px] font-bold text-brand-700 hover:text-brand-800">Mark all read</button> : null}
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-[#f8fbff] p-3 md:p-4">
          {loading ? <div className="space-y-2">{[1, 2, 3].map((n) => <div key={n} className="animate-pulse rounded-xl border border-slate-100 bg-white p-4"><div className="h-3 w-40 rounded bg-slate-100" /><div className="mt-2 h-3 w-full rounded bg-slate-100" /><div className="mt-2 h-2 w-24 rounded bg-slate-100" /></div>)}</div> : visibleItems.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white px-5 py-10 text-center">
              <p className="text-sm font-bold text-ink-900">No items in this view</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">Your current filter has no academic actions waiting for you.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {visibleItems.map((item) => {
                const meta = CATEGORY_META[item.category ?? "information"];
                const displayStudent = item.roll_number || item.student_name || item.student_id;
                const statusText = item.category === "follow_up" ? "FOLLOW-UP" : meta.label.toUpperCase();
                return (
                  <article key={item.id} className={`rounded-xl border bg-white p-4 ${item.is_read ? "border-slate-200" : "border-[#cfe0f8] shadow-sm"}`}>
                    <div className="flex items-start gap-3">
                      <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${item.category === "action_required" ? "bg-red-500" : item.category === "follow_up" ? "bg-amber-500" : item.category === "escalation" ? "bg-brand-600" : "bg-slate-300"}`} aria-hidden="true" />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="break-words text-sm font-extrabold text-ink-900">{item.risk_label ?? item.title ?? "Academic action"}{displayStudent ? ` · ${displayStudent}` : ""}</p>
                            <div className="mt-1 flex flex-wrap items-center gap-1.5">
                              <span className={`rounded-md border px-1.5 py-0.5 text-[9px] font-extrabold tracking-wide ${meta.className}`}>{statusText}</span>
                              {item.risk_level ? <span className="text-[10px] font-semibold text-slate-500">{item.risk_level}</span> : null}
                              {typeof item.priority_score === "number" && item.priority_score > 0 ? <span className="text-[10px] font-semibold text-slate-500">Priority {Math.round(item.priority_score)}/100</span> : null}
                            </div>
                          </div>
                          <span className="shrink-0 text-[10px] font-medium text-slate-400">{timeAgo(item.created_at)}</span>
                        </div>
                        {item.section ? <p className="mt-1 text-[10px] font-semibold text-slate-400">{item.department ?? "CSE"} · {item.section}</p> : null}
                        {item.evidence ? <p className="mt-3 text-xs font-semibold leading-5 text-slate-700">{item.evidence}</p> : null}
                        <p className="mt-2 text-xs leading-5 text-slate-600">{item.recommended_action ? item.recommended_action : item.message ?? "Review the associated academic case."}</p>
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          {item.student_id ? <button type="button" onClick={() => void openNotification(item)} className="ui-button ui-button-primary !min-h-9 !px-3 !text-xs">Review case</button> : null}
                          {!item.is_read ? <button type="button" onClick={() => void markRead(item.id)} className="text-[10px] font-bold text-brand-700 hover:text-brand-800">Mark as read</button> : null}
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
        
      </div>
    </>
  ) : null;

  return (
    <div ref={panelRef} className="relative">
      <button
        type="button"
        className={`relative grid h-10 w-10 place-items-center rounded-xl border bg-white text-slate-600 transition ${open ? "border-brand-300 bg-brand-50 text-brand-700" : "border-slate-200 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"}`}
        aria-label={`Academic action center${unread ? `, ${unread} unread` : ""}`}
        aria-expanded={open}
        aria-controls="academic-action-center"
        onClick={() => setOpen((current) => !current)}
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 9a6 6 0 0 0-12 0c0 6-2.5 6-2.5 7.5h15C18.5 15 18 15 18 9Z" /><path d="M10 20h4" /></svg>
        {unread > 0 ? <span className="absolute -right-1 -top-1 grid min-h-4 min-w-4 place-items-center rounded-full bg-red-600 px-1 text-[9px] font-bold text-white">{unread > 9 ? "9+" : unread}</span> : null}
      </button>
      {typeof document !== "undefined" && panel ? createPortal(panel, document.body) : null}
    </div>
  );

}

export default function InstitutionalShell({ children, eyebrow, title, subtitle }: Props) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const role = user?.role ?? "mentor";
  const links = NAV[role] ?? [];
  const profileActive = location.pathname.startsWith("/mentor/student/");
  const roleLabel = ROLE_LABEL[role] ?? role;
  const initials = useMemo(() => (user?.name || roleLabel).split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase(), [user?.name, roleLabel]);

  return (
    <div className="min-h-screen bg-canvas">
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="institutional-header-inner mx-auto max-w-[1600px] px-4 py-3 sm:px-6 lg:px-8">
          <div className="grid gap-3 md:grid-cols-[1fr_auto] lg:grid-cols-[270px_minmax(0,1fr)_430px] lg:items-center lg:gap-4">
            <div className="institutional-header-brand flex min-w-0 items-center gap-3">
              <img src="/branding/vignan-brand.png" alt="Vignan's University" className="h-12 w-auto max-w-[220px] object-contain sm:h-14" />
            </div>
            <div className="institutional-header-tools flex min-w-0 flex-wrap items-center justify-end gap-3 lg:col-start-3 lg:row-start-1">
              <img src="/branding/accreditation-badges.png" alt="Institutional accreditation badges" className="hidden h-10 w-auto object-contain xl:block" />
              {role !== "admin" ? <NotificationBell /> : null}
              <div className="hidden min-w-0 max-w-[180px] items-center gap-2 sm:flex">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#eaf2ff] text-xs font-extrabold text-brand-700">{initials}</div>
                <div className="min-w-0">
                  <p className="max-w-[130px] truncate text-xs font-bold text-ink-900">{user?.name ?? "Staff user"}</p>
                  <p className="max-w-[130px] truncate text-[11px] font-medium text-slate-500">{roleLabel}</p>
                </div>
              </div>
              <button type="button" onClick={logout} className="shrink-0 whitespace-nowrap rounded-full border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700">Sign out</button>
            </div>
            <div className="institutional-header-title hidden min-w-0 items-center justify-center border-x border-slate-100 px-5 lg:col-start-2 lg:row-start-1 lg:flex">
              <div className="min-w-0 text-center">
                <p className="truncate text-[10px] font-bold uppercase tracking-[0.26em] text-slate-400">{eyebrow}</p>
                <h1 className="mt-1 truncate text-lg font-extrabold tracking-wide text-[#18345f]">{title}</h1>
                {subtitle ? <p className="mt-1 truncate text-xs text-slate-500">{subtitle}</p> : null}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1600px] px-4 pt-3 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white px-2.5 py-2 shadow-[0_1px_2px_rgba(30,41,59,0.03)] sm:flex-row sm:items-center sm:justify-between sm:px-3">
          <nav aria-label="Primary navigation" className="institutional-nav flex min-w-0 items-center gap-1 overflow-x-auto pb-0.5">
            {links.map((link) => {
              const active = location.pathname === link.to;
              return <Link key={link.to} to={link.to} aria-current={active ? "page" : undefined} className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold transition ${active ? "bg-[#edf4ff] text-brand-700" : "text-slate-600 hover:bg-slate-50 hover:text-ink-900"}`}><span aria-hidden="true" className="text-sm">{link.icon}</span>{link.label}</Link>;
            })}
            {profileActive ? <span className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-[#edf4ff] px-3 py-2 text-xs font-bold text-brand-700"><span aria-hidden="true">◉</span>Student case</span> : null}
          </nav>
          <div className="hidden shrink-0 items-center gap-2 text-[11px] font-semibold text-slate-500 md:flex"><span className="h-2 w-2 rounded-full bg-emerald-500" /> 2026–27 · Semester 5</div>
        </div>
      </div>

      <main id="main-content" className="mx-auto max-w-[1600px] px-4 py-5 sm:px-6 lg:px-8">
        <div className="mb-4 lg:hidden">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">{eyebrow}</p>
          <h1 className="mt-1 text-xl font-extrabold tracking-tight text-[#18345f] sm:text-2xl">{title}</h1>
          {subtitle ? <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">{subtitle}</p> : null}
        </div>
        {children}
      </main>
      <footer className="border-t border-slate-200 bg-white/80 px-4 py-5 text-center text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400">
        <span className="block">Vignan's University · Student Academic Risk Management</span>
        <span className="mt-1 block text-[9px] normal-case tracking-normal text-slate-400">CSE academic systems · authorized faculty and institutional authorities</span>
      </footer>
    </div>
  );
}
