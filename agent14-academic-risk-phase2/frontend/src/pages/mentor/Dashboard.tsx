import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import RiskBadge, { scoreToLevel } from "../../components/RiskBadge";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import { acknowledgeAlert, getWatchlist, updateIntervention, type MentorAlert } from "../../features/mentor/api";
import { readableRiskType, scorePercent } from "../../features/mentor/formatters";

function Metric({ label, value, detail, tone = "text-ink-900" }: { label: string; value: number | string; detail: string; tone?: string }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-bold tracking-tight ${tone}`}>{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </Card>
  );
}

interface StudentWatchlistRow {
  student_id: string;
  student_name: string;
  alerts: MentorAlert[];
  primary: MentorAlert;
}

function groupAlertsByStudent(items: MentorAlert[]): StudentWatchlistRow[] {
  const grouped = new Map<string, MentorAlert[]>();
  for (const item of items) {
    const alerts = grouped.get(item.student_id) ?? [];
    alerts.push(item);
    grouped.set(item.student_id, alerts);
  }
  return [...grouped.values()]
    .map((alerts) => ({
      student_id: alerts[0].student_id,
      student_name: alerts[0].student_name,
      alerts,
      primary: [...alerts].sort((left, right) => right.priority_score - left.priority_score)[0],
    }))
    .sort((left, right) => right.primary.priority_score - left.primary.priority_score);
}

export default function MentorDashboard() {
  const { user, logout } = useAuth();
  const [items, setItems] = useState<MentorAlert[]>([]);
  const [assignedStudents, setAssignedStudents] = useState(0);
  const [openAlerts, setOpenAlerts] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<MentorAlert | null>(null);
  const [interventionStatus, setInterventionStatus] = useState<"ACKNOWLEDGED" | "ACTION_TAKEN" | "FOLLOW_UP" | "RESOLVED">("ACTION_TAKEN");
  const [interventionNotes, setInterventionNotes] = useState("");
  const [savingIntervention, setSavingIntervention] = useState(false);

  useEffect(() => {
    getWatchlist()
      .then((data) => {
        setItems(data.items);
        setAssignedStudents(data.assigned_students);
        setOpenAlerts(data.open_alerts);
      })
      .catch(() => setError("The mentor watchlist could not be loaded. Check that the backend is running."))
      .finally(() => setLoading(false));
  }, []);

  async function handleAcknowledge(alertId: string) {
    const updated = await acknowledgeAlert(alertId);
    setItems((current) => current.map((item) => item.alert_id === alertId ? { ...item, status: updated.status } : item));
    setOpenAlerts((current) => Math.max(0, current - 1));
  }

  async function handleIntervention(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedAlert) return;
    setSavingIntervention(true);
    try {
      const updated = await updateIntervention(selectedAlert.alert_id, interventionStatus, interventionNotes);
      setItems((current) => current.map((item) => item.alert_id === selectedAlert.alert_id ? { ...item, status: updated.status } : item));
      if (interventionStatus === "RESOLVED") setOpenAlerts((current) => Math.max(0, current - 1));
      setSelectedAlert(null);
      setInterventionNotes("");
    } catch {
      setError("The intervention could not be saved. Please try again.");
    } finally {
      setSavingIntervention(false);
    }
  }

  const critical = items.filter((item) => item.risk_score >= 75).length;
  const high = items.filter((item) => item.risk_score >= 50 && item.risk_score < 75).length;
  const newAlerts = items.filter((item) => item.status === "NEW").length;
  const groupedItems = groupAlertsByStudent(items);
  const columns: TableColumn<StudentWatchlistRow>[] = [
    { key: "student", header: "Student", render: (item) => <Link to={`/mentor/student/${item.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{item.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{item.student_id}</span></Link> },
    { key: "risk", header: "Risk profile", render: (item) => <div className="flex max-w-[280px] flex-wrap items-center gap-1.5"><RiskBadge level={scoreToLevel(item.primary.risk_score)} /><span className="text-xs font-semibold text-slate-600">{readableRiskType(item.primary.risk_type)}</span>{item.alerts.length > 1 ? <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-500">+{item.alerts.length - 1} more</span> : null}</div> },
    { key: "score", header: "Highest risk", render: (item) => <span className="font-bold text-ink-900">{scorePercent(item.primary.risk_score)}</span> },
    { key: "priority", header: "Priority", render: (item) => <span className="font-semibold text-brand-700">{scorePercent(item.primary.priority_score)}</span> },
    { key: "status", header: "Alert status", render: (item) => <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.alerts.filter((alert) => alert.status !== "RESOLVED").length} open · {item.alerts.filter((alert) => alert.status === "NEW").length} new</span> },
    { key: "action", header: "Action", render: (item) => <button type="button" onClick={() => setSelectedAlert(item.primary)} className="font-semibold text-brand-600 hover:text-brand-700">Review alerts</button> },
  ];

  return (
    <main className="min-h-screen bg-canvas">
      <header className="border-b border-slate-200 bg-white px-5 py-4 md:px-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-5">
          <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-600">Mentor workspace</p><h1 className="mt-1 text-2xl font-bold tracking-tight text-ink-900">Good morning, {user?.name ?? "Mentor"}</h1><p className="mt-1 text-sm text-slate-500">Which of your students needs attention first?</p></div>
          <button type="button" onClick={logout} className="text-sm font-semibold text-slate-500 hover:text-ink-900">Sign out</button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-6 px-5 py-6 md:px-8">
        {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Mentor summary">
          <Metric label="Assigned students" value={assignedStudents} detail="Students in your cohort" />
          <Metric label="Critical cases" value={critical} detail="Require immediate attention" tone="text-red-700" />
          <Metric label="High-risk cases" value={high} detail="Priority support queue" tone="text-orange-700" />
          <Metric label="Open alerts" value={openAlerts} detail={`${newAlerts} new and awaiting review`} tone="text-brand-700" />
        </section>

        <Card as="section" className="p-0">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Priority queue</p><h2 className="mt-1 text-lg font-bold text-ink-900">Students requiring support</h2></div>
            <p className="text-xs text-slate-500">Sorted by priority and risk severity</p>
          </div>
          <div className="p-3 md:p-5">
            {loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading your watchlist...</p> : <Table columns={columns} rows={groupedItems} rowKey={(item) => item.student_id} caption="Mentor priority watchlist" emptyMessage="No active alerts in your assigned cohort." />}
          </div>
        </Card>

        {selectedAlert ? (
          <Card as="section" className="border-brand-200 bg-brand-50/40">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-600">Intervention record</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedAlert.student_name} · {readableRiskType(selectedAlert.risk_type)}</h2><p className="mt-1 text-sm text-slate-500">Record the support action and the next state for this alert.</p></div>
              <div className="flex items-center gap-3">
                {selectedAlert.status === "NEW" ? <button type="button" onClick={() => void handleAcknowledge(selectedAlert.alert_id)} className="text-sm font-semibold text-brand-600 hover:text-brand-700">Acknowledge</button> : null}
                <button type="button" onClick={() => setSelectedAlert(null)} className="text-sm font-semibold text-slate-500 hover:text-ink-900">Cancel</button>
              </div>
            </div>
            <form onSubmit={(event) => void handleIntervention(event)} className="mt-4 grid gap-3 md:grid-cols-[220px_1fr_auto] md:items-end">
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Next status<select value={interventionStatus} onChange={(event) => setInterventionStatus(event.target.value as typeof interventionStatus)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900"><option value="ACKNOWLEDGED">Acknowledged</option><option value="ACTION_TAKEN">Action taken</option><option value="FOLLOW_UP">Follow-up</option><option value="RESOLVED">Resolved</option></select></label>
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Notes<textarea required value={interventionNotes} onChange={(event) => setInterventionNotes(event.target.value)} placeholder="Describe the mentor action or follow-up plan" className="min-h-10 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900" /></label>
              <button type="submit" disabled={savingIntervention} className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">{savingIntervention ? "Saving..." : "Save intervention"}</button>
            </form>
          </Card>
        ) : null}
      </div>
    </main>
  );
}
