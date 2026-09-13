import { useMemo, useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

interface NotificationItem {
  id: string;
  title?: string;
  message?: string;
  is_read?: boolean;
  created_at?: string;
  notification_type?: string;
}

interface NotificationResponse {
  items: NotificationItem[];
  unread_count?: number;
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

function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);

  async function loadNotifications() {
    setLoading(true);
    try {
      const response = await api.get<NotificationResponse>("/notifications", { params: { limit: 6 } });
      setItems(response.data.items ?? []);
      setUnread(response.data.unread_count ?? (response.data.items ?? []).filter((item) => !item.is_read).length);
    } catch {
      // Notifications are additive to the workspace; do not block the main UI.
    } finally {
      setLoading(false);
    }
  }

  // Lazy-load: only fetch notifications the first time the bell is opened,
  // instead of on every page mount, to keep initial page load light.
  function toggleOpen() {
    setOpen((current) => {
      const next = !current;
      if (next && !hasLoaded) {
        setHasLoaded(true);
        void loadNotifications();
      }
      return next;
    });
  }

  async function markRead(id: string) {
    try {
      await api.patch(`/notifications/${id}/read`);
      setItems((current) => current.map((item) => item.id === id ? { ...item, is_read: true } : item));
      setUnread((count) => Math.max(0, count - 1));
    } catch {
      // Keep notification UI resilient when the notification service is unavailable.
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        className="relative grid h-10 w-10 shrink-0 place-items-center rounded-full border border-slate-200 bg-white text-slate-600 transition duration-150 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"
        aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
        onClick={toggleOpen}
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M18 9a6 6 0 0 0-12 0c0 6-2.5 6-2.5 7.5h15C18.5 15 18 15 18 9Z" />
          <path d="M10 20h4" />
        </svg>
        {unread > 0 ? <span className="absolute -right-0.5 -top-0.5 grid min-h-4 min-w-4 place-items-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">{unread > 9 ? "9+" : unread}</span> : null}
      </button>
      {open ? (
        <div className="animate-slide-down absolute right-0 top-12 z-50 flex max-h-[min(28rem,80vh)] w-[min(360px,calc(100vw-32px))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
          <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-4 py-3">
            <div><p className="text-sm font-bold text-ink-900">Notifications</p><p className="text-[11px] text-slate-500">Academic risk actions and follow-ups</p></div>
            <span className="text-[11px] font-semibold text-brand-700">{unread} unread</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? <p className="px-4 py-6 text-center text-xs text-slate-500">Loading notifications…</p> : items.length === 0 ? <p className="px-4 py-8 text-center text-xs text-slate-500">No notifications right now.</p> : items.map((item) => (
              <button key={item.id} type="button" onClick={() => void markRead(item.id)} className={`block w-full border-b border-slate-50 px-4 py-3 text-left transition duration-150 hover:bg-brand-50 ${item.is_read ? "bg-white" : "bg-brand-50/40"}`}>
                <div className="flex items-start gap-3"><span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${item.is_read ? "bg-slate-300" : "bg-brand-500"}`} /><div className="min-w-0"><p className="text-xs font-semibold text-ink-900">{item.title ?? "Academic risk notification"}</p><p className="mt-1 text-xs leading-5 text-slate-600">{item.message ?? "Review the associated student or intervention record."}</p><p className="mt-1 text-[10px] font-medium text-slate-400">{timeAgo(item.created_at)}</p></div></div>
              </button>
            ))}
          </div>
        </div>
      ) : null}
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
      <div className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto grid min-h-[86px] max-w-[1600px] grid-cols-1 items-center gap-4 px-4 py-3 sm:px-6 lg:grid-cols-[270px_1fr_360px] lg:px-8">
          <div className="flex items-center gap-3">
            <img src="/branding/vignan-brand.png" alt="Vignan's University" className="h-14 w-auto object-contain" />
          </div>
          <div className="hidden self-stretch items-center justify-center border-x border-slate-100 px-6 lg:flex">
            <div className="text-center">
              <p className="text-[10px] font-bold uppercase tracking-[0.26em] text-slate-400">{eyebrow}</p>
              <h1 className="mt-1 text-lg font-extrabold tracking-wide text-[#18345f]">{title}</h1>
              {subtitle ? <p className="mt-1 text-xs text-slate-500">{subtitle}</p> : null}
            </div>
          </div>
          <div className="flex flex-nowrap items-center justify-between gap-3 lg:justify-end">
            <img src="/branding/accreditation-badges.png" alt="Institutional accreditation badges" className="hidden h-12 w-auto shrink-0 object-contain xl:block" />
            {role !== "admin" ? <NotificationBell /> : null}
            <div className="hidden items-center gap-2 sm:flex">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#eaf2ff] text-xs font-extrabold text-brand-700">{initials}</div>
              <div className="min-w-0">
                <p className="max-w-[150px] truncate text-xs font-bold text-ink-900">{user?.name ?? "Staff user"}</p>
                <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400">{roleLabel}</p>
              </div>
            </div>
            <button type="button" onClick={logout} className="shrink-0 whitespace-nowrap rounded-full border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 transition duration-150 hover:border-red-200 hover:bg-red-50 hover:text-red-700">Sign out</button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 pt-3 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-[0_1px_2px_rgba(30,41,59,0.03)]">
          <nav aria-label="Primary navigation" className="flex max-w-full flex-nowrap items-center gap-1 overflow-x-auto">
            {links.map((link) => {
              const active = location.pathname === link.to;
              return <Link key={link.to} to={link.to} className={`inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-xs font-bold transition duration-150 ${active ? "bg-[#edf4ff] text-brand-700" : "text-slate-600 hover:bg-slate-50 hover:text-ink-900"}`}><span aria-hidden="true" className="text-sm">{link.icon}</span>{link.label}</Link>;
            })}
            {profileActive ? <span className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl bg-[#edf4ff] px-3 py-2 text-xs font-bold text-brand-700"><span aria-hidden="true">◉</span>Student profile</span> : null}
          </nav>
          <div className="hidden shrink-0 items-center gap-2 whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 md:flex"><span className="h-2 w-2 shrink-0 rounded-full bg-emerald-500" /> Early warning system · current academic cycle</div>
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 py-5 sm:px-6 lg:px-8">
        <div className="mb-4 lg:hidden">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">{eyebrow}</p>
          {/* The desktop header above already renders the page's single <h1>.
              This mobile-only duplicate must not be a second h1 (bad for a11y/SEO),
              so it's rendered as a paragraph styled to match. */}
          <p role="heading" aria-level={1} className="mt-1 text-xl font-extrabold tracking-tight text-[#18345f]">{title}</p>
          {subtitle ? <p className="mt-1 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
        <div className="animate-fade-in">{children}</div>
      </div>
      <footer className="border-t border-slate-200 bg-white/80 px-4 py-4 text-center text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400">
        Vignan's University · Student Academic Risk Management · CSE Academic Systems
      </footer>
    </div>
  );
}