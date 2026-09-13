import { useEffect, useMemo, useState } from "react";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import RiskBadge, { scoreToLevel } from "../../components/RiskBadge";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import { acknowledgeAlert, getMentorWorkspace, updateIntervention, type MentorAlert, type MentorStudentRow } from "../../features/mentor/api";
import { readableRiskType, scorePercent } from "../../features/mentor/formatters";

function Metric({ icon, label, value, detail, tone = "text-ink-900" }: { icon: string; label: string; value: number | string; detail: string; tone?: string }) {
  return (
    <Card className="p-5">
      <p className="text-xl" aria-hidden="true">{icon}</p>
      <p className="mt-3 text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-bold tracking-tight ${tone}`}>{value}</p>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </Card>
  );
}

function getRiskReason(row: MentorStudentRow) {
  return row.primary_risk ? readableRiskType(row.primary_risk) : "No elevated risk signal";
}

function getRecommendedAction(row: MentorStudentRow) {
  if (row.primary_alert?.suggested_action) return row.primary_alert.suggested_action;
  switch (row.primary_risk) {
    case "attendance_shortage": return "Review attendance barrier and recovery plan.";
    case "backlog": return "Review backlog clearance plan.";
    case "gpa_threshold": return "Set an academic improvement target.";
    case "course_failure": return "Review course performance and recovery plan.";
    case "discontinuation": return "Coordinate support follow-up and monitor continuity.";
    default: return "Review student profile.";
  }
}

export default function MentorDashboard() {
  const { user } = useAuth();
  const [workspace, setWorkspace] = useState<Awaited<ReturnType<typeof getMentorWorkspace>> | null>(null);
  const [rows, setRows] = useState<MentorStudentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [actionOnly, setActionOnly] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<MentorAlert | null>(null);
  const [interventionStatus, setInterventionStatus] = useState<"ACKNOWLEDGED" | "ACTION_TAKEN" | "FOLLOW_UP" | "RESOLVED">("ACTION_TAKEN");
  const [interventionNotes, setInterventionNotes] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [savingIntervention, setSavingIntervention] = useState(false);

  async function loadWorkspace() {
    setLoading(true);
    try {
      const data = await getMentorWorkspace({
        q: search || undefined,
        risk_type: riskFilter === "all" ? undefined : riskFilter,
        severity: severityFilter === "all" ? undefined : severityFilter,
        needs_action: actionOnly ? true : undefined,
      });
      setWorkspace(data);
      setRows(data.items);
      setError(null);
    } catch {
      setError("The mentor workspace could not be loaded. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => void loadWorkspace(), 300);
    return () => window.clearTimeout(timer);
  }, [search, riskFilter, severityFilter, actionOnly]);

  async function handleAcknowledge(alertId: string) {
    try {
      await acknowledgeAlert(alertId);
      await loadWorkspace();
      setSelectedAlert(null);
    } catch {
      setError("The alert could not be acknowledged. Please try again.");
    }
  }

  async function handleIntervention(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedAlert || !interventionNotes.trim()) return;
    if (interventionStatus === "FOLLOW_UP" && !followUpDate) {
      setError("Choose a follow-up date before saving a follow-up intervention.");
      return;
    }
    setSavingIntervention(true);
    try {
      await updateIntervention(selectedAlert.alert_id, interventionStatus, interventionNotes.trim(), followUpDate || undefined);
      await loadWorkspace();
      setSelectedAlert(null);
      setInterventionNotes("");
      setFollowUpDate("");
    } catch {
      setError("The intervention could not be saved. Please try again.");
    } finally {
      setSavingIntervention(false);
    }
  }

  const filterLabel = useMemo(() => {
    if (actionOnly) return "Students requiring action";
    if (riskFilter !== "all") return readableRiskType(riskFilter);
    return "All assigned students";
  }, [actionOnly, riskFilter]);

  const columns: TableColumn<MentorStudentRow>[] = [
    {
      key: "student",
      header: "Student",
      render: (row) => (
        <Link to={`/mentor/student/${row.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">
          {row.student_name}
          <span className="mt-0.5 block text-xs font-normal text-slate-400">{row.student_id} · {row.section}</span>
        </Link>
      ),
    },
    {
      key: "risk",
      header: "Primary risk",
      render: (row) => (
        <div className="flex max-w-[250px] flex-wrap items-center gap-2">
          <RiskBadge level={scoreToLevel(row.risk_score)} />
          <span className="text-xs font-semibold text-slate-600">{getRiskReason(row)}</span>
        </div>
      ),
    },
    { key: "riskScore", header: "Risk", render: (row) => <span className="font-bold text-ink-900">{scorePercent(row.risk_score)}</span> },
    { key: "priority", header: "Priority", render: (row) => <span className="font-semibold text-brand-700">{scorePercent(row.priority_score)}</span> },
    {
      key: "alerts",
      header: "Alerts",
      render: (row) => <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{row.open_alerts} open · {row.new_alerts} new</span>,
    },
    {
      key: "recommendation",
      header: "Recommended action",
      render: (row) => <span className="block max-w-[300px] whitespace-normal text-sm text-slate-600">{getRecommendedAction(row)}</span>,
    },
    {
      key: "action",
      header: "Action",
      render: (row) => (
        <div className="flex items-center gap-3">
          <Link to={`/mentor/student/${row.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open</Link>
          {row.primary_alert ? <button type="button" onClick={() => setSelectedAlert(row.primary_alert)} className="font-semibold text-slate-600 hover:text-ink-900">Intervene</button> : null}
        </div>
      ),
    },
  ];

  return (
    <InstitutionalShell
      eyebrow="CSE · VIGNAN'S UNIVERSITY"
      title="STUDENT ACADEMIC RISK MANAGEMENT"
      subtitle="Mentor Workspace · Early warning and intervention queue"
    >
      <div className="space-y-6">
      <WorkspaceIntro role="mentor" name={user?.name} context={workspace?.risk_source} />
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-ink-900">Good morning, {user?.name ?? "Mentor"}</h2>
            <p className="mt-1 text-sm text-slate-500">Review your assigned students by risk, priority, and intervention status.</p>
          </div>
        </div>

        {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Mentor summary">
          <Metric icon="👥" label="Assigned students" value={workspace?.assigned_students ?? 0} detail="Students in your cohort" />
          <Metric icon="🚨" label="Critical students" value={workspace?.critical_students ?? 0} detail="At least one critical risk" tone="text-red-700" />
          <Metric icon="⚠️" label="High-risk students" value={workspace?.high_risk_students ?? 0} detail="High or critical risk" tone="text-orange-700" />
          <Metric icon="🎯" label="Needs action" value={workspace?.students_needing_action ?? 0} detail="Canonical alert policy" tone="text-brand-700" />
          <Metric icon="📬" label="Open alerts" value={workspace?.open_alerts ?? 0} detail={`${workspace?.new_alerts ?? 0} new`} tone="text-brand-700" />
        </section>

        <Card as="section" className="p-0">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Mentor queue</p><h2 className="mt-1 text-lg font-bold text-ink-900">{filterLabel}</h2></div>
            <span className="text-xs text-slate-500">Source: {workspace?.risk_source ?? "canonical risk predictions"}</span>
          </div>
          <div className="grid gap-3 border-b border-slate-100 px-5 py-4 md:grid-cols-[1fr_190px_150px_auto]">
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Student name or ID" className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900 transition-colors duration-150 focus:border-brand-400" /></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Risk type<select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900 transition-colors duration-150 focus:border-brand-400"><option value="all">All risks</option><option value="course_failure">Course failure</option><option value="backlog">Backlog</option><option value="gpa_threshold">GPA threshold</option><option value="attendance_shortage">Attendance shortage</option><option value="discontinuation">Support attention</option></select></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Severity<select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900 transition-colors duration-150 focus:border-brand-400"><option value="all">All levels</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="MODERATE">Moderate</option><option value="LOW">Low</option></select></label>
            <label className="flex items-center gap-2 self-end rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"><input type="checkbox" checked={actionOnly} onChange={(event) => setActionOnly(event.target.checked)} /> Needs action</label>
          </div>
          <div className="p-3 md:p-5">
            {loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading your mentor queue...</p> : <Table columns={columns} rows={rows} rowKey={(row) => row.student_id} caption="Mentor student queue" emptyMessage="No students match the current filters." />}
          </div>
        </Card>

        {selectedAlert ? (
          <Card as="section" className="border-brand-200 bg-brand-50/40">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-600">Intervention record</p>
                <h2 className="mt-1 text-lg font-bold text-ink-900">{selectedAlert.student_name} · {readableRiskType(selectedAlert.risk_type)}</h2>
                <p className="mt-1 text-sm text-slate-500">Priority {scorePercent(selectedAlert.priority_score)} · Risk {scorePercent(selectedAlert.risk_score)} · {selectedAlert.risk_level ?? "current"}</p>
              </div>
              <div className="flex items-center gap-3">
                {selectedAlert.status === "NEW" ? <button type="button" onClick={() => void handleAcknowledge(selectedAlert.alert_id)} className="text-sm font-semibold text-brand-600 hover:text-brand-700">Acknowledge</button> : null}
                <button type="button" onClick={() => setSelectedAlert(null)} className="text-sm font-semibold text-slate-500 hover:text-ink-900">Cancel</button>
              </div>
            </div>
            <form onSubmit={(event) => void handleIntervention(event)} className="mt-4 grid gap-3 md:grid-cols-[190px_190px_1fr_auto] md:items-end">
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Next status<select value={interventionStatus} onChange={(event) => setInterventionStatus(event.target.value as typeof interventionStatus)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900"><option value="ACKNOWLEDGED">Acknowledged</option><option value="ACTION_TAKEN">Action taken</option><option value="FOLLOW_UP">Follow-up</option><option value="RESOLVED">Resolved</option></select></label>
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Follow-up date<input required={interventionStatus === "FOLLOW_UP"} type="date" min={new Date().toISOString().slice(0, 10)} value={followUpDate} onChange={(event) => setFollowUpDate(event.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900" /></label>
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Notes<textarea required value={interventionNotes} onChange={(event) => setInterventionNotes(event.target.value)} placeholder="Describe the mentor action or next follow-up" className="min-h-10 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900" /></label>
              <button type="submit" disabled={savingIntervention || !interventionNotes.trim()} className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">{savingIntervention ? "Saving..." : "Save intervention"}</button>
            </form>
          </Card>
        ) : null}
      </div>
    </InstitutionalShell>
  );
}