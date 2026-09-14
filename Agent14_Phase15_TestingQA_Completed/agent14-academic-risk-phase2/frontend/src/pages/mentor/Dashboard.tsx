import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import RiskBadge from "../../components/RiskBadge";
import Table, { type TableColumn } from "../../components/Table";
import { ActionButton, Icon, MetricCard, SectionHeading } from "../../components/AcademicUI";
import { useAuth } from "../../context/AuthContext";
import { acknowledgeAlert, getMentorWorkspace, markStudentCaseComplete, updateIntervention, type MentorAlert, type MentorStudentRow } from "../../features/mentor/api";
import { readableRiskType } from "../../features/mentor/formatters";
import { notifyCaseWorkUpdated, subscribeToCaseWorkUpdates, subscribeToLiveCaseWorkUpdates } from "../../features/caseWorkEvents";
import CompleteCaseDialog, { type CompletionPayload } from "../../components/CompleteCaseDialog";

function riskLevelLabel(level: string) {
  const normalized = level?.toUpperCase();
  return normalized === "MEDIUM" ? "MODERATE" : normalized || "LOW";
}

function score100(value: number) {
  return `${Math.round(value)} / 100`;
}

function getRecommendedAction(row: MentorStudentRow) {
  if (!row.needs_action) return "Monitor";
  if (row.primary_alert?.suggested_action) return row.primary_alert.suggested_action;
  switch (row.primary_risk) {
    case "attendance_shortage": return "Review attendance barrier and agree on a recovery target.";
    case "backlog": return "Review backlog clearance plan.";
    case "gpa_threshold": return "Set a realistic academic improvement target.";
    case "course_failure": return "Review the affected course and agree on a recovery step.";
    case "support_attention": return "Coordinate supportive follow-up and continuity review.";
    default: return "Review the student case.";
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
  const [completingAlertId, setCompletingAlertId] = useState<string | null>(null);
  const [completedStudents, setCompletedStudents] = useState<Set<string>>(new Set());
  const [completionTarget, setCompletionTarget] = useState<MentorStudentRow | null>(null);
  const [page, setPage] = useState(1);

  async function loadWorkspace() {
    setLoading(true);
    try {
      const data = await getMentorWorkspace({
        q: search || undefined,
        risk_type: riskFilter === "all" ? undefined : riskFilter,
        severity: severityFilter === "all" ? undefined : severityFilter,
        needs_action: actionOnly ? true : undefined,
        page, page_size: 25,
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

  useEffect(() => { setPage(1); }, [search, riskFilter, severityFilter, actionOnly]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadWorkspace(), 160);
    return () => window.clearTimeout(timer);
  }, [search, riskFilter, severityFilter, actionOnly, page]);

  useEffect(() => {
    const stop = subscribeToCaseWorkUpdates(() => void loadWorkspace());
    const stopLive = subscribeToLiveCaseWorkUpdates(() => void loadWorkspace());
    const timer = window.setInterval(() => void loadWorkspace(), 15000);
    return () => { stop(); stopLive(); window.clearInterval(timer); };
  }, [search, riskFilter, severityFilter, actionOnly, page]);

  async function handleAcknowledge(alertId: string) {
    try {
      await acknowledgeAlert(alertId);
      await loadWorkspace();
      setSelectedAlert(null);
    } catch {
      setError("The alert could not be acknowledged. Please try again.");
    }
  }

  async function handleMarkComplete(row: MentorStudentRow, payload: CompletionPayload) {
    setCompletingAlertId(row.student_id);
    setError(null);
    try {
      const result = await markStudentCaseComplete(row.student_id, payload);
      setCompletedStudents((current) => new Set(current).add(row.student_id));
      setCompletionTarget(null);
      notifyCaseWorkUpdated();
      await loadWorkspace();
      if (selectedAlert?.student_id === row.student_id) setSelectedAlert(null);
    } catch {
      setError("The student case could not be marked as complete. Please try again.");
    } finally {
      setCompletingAlertId(null);
    }
  }

  async function handleIntervention(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedAlert || !interventionNotes.trim()) return;
    if (interventionStatus === "FOLLOW_UP" && !followUpDate) {
      setError("Choose a follow-up date before saving a follow-up action.");
      return;
    }
    setSavingIntervention(true);
    try {
      await updateIntervention(selectedAlert.alert_id, interventionStatus, interventionNotes.trim(), followUpDate || undefined);
      await loadWorkspace();
      setSelectedAlert(null);
      setInterventionNotes("");
      setFollowUpDate("");
      setError(null);
    } catch {
      setError("The intervention could not be saved. Please try again.");
    } finally {
      setSavingIntervention(false);
    }
  }

  const filterLabel = useMemo(() => {
    if (actionOnly) return "Students requiring action";
    if (riskFilter !== "all") return readableRiskType(riskFilter);
    if (severityFilter !== "all") return `${riskLevelLabel(severityFilter)} risk students`;
    return "Assigned students";
  }, [actionOnly, riskFilter, severityFilter]);

  const columns: TableColumn<MentorStudentRow>[] = [
    {
      key: "student",
      header: "Student",
      render: (row) => (
        <Link to={`/mentor/student/${row.student_id}`} className="group block min-w-0">
          <span className="block break-words font-semibold text-ink-900 group-hover:text-brand-700">{row.student_name}</span>
          <span className="mt-1 block text-xs font-medium text-slate-500">{row.roll_number ?? row.student_id} · {row.section}</span>
        </Link>
      ),
    },
    {
      key: "concern",
      header: "Primary concern",
      render: (row) => (
        <div className="min-w-0">
          <RiskBadge level={riskLevelLabel(row.risk_level) as any} />
          <div className="mt-2 flex min-w-0 flex-wrap gap-1.5">
            {(row.risk_breakdown ?? []).map((risk) => (
              <span key={`${risk.risk_type}-${risk.course_ids.join("-")}`} title={`${risk.risk_label} · ${risk.risk_level} · ${Math.round(risk.risk_score)}/100`} className="rounded-full border border-slate-200 bg-white px-2 py-1 text-[10px] font-bold text-slate-700">
                {risk.risk_label}{risk.course_ids.length ? ` · ${risk.course_ids.join(", ")}` : ""}
              </span>
            ))}
            {!row.risk_breakdown?.length ? <span className="text-sm font-semibold text-slate-500">No elevated risk</span> : null}
          </div>
        </div>
      ),
    },
    {
      key: "risk",
      header: "Risk",
      render: (row) => <div><p className="font-extrabold text-ink-900">{score100(row.risk_score)}</p><p className="mt-1 text-[11px] text-slate-500">Risk / 100</p></div>,
    },
    {
      key: "priority",
      header: "Priority",
      render: (row) => <div><p className="font-extrabold text-brand-700">{score100(row.priority_score)}</p><p className="mt-1 text-[11px] text-slate-500">Priority / 100</p></div>,
    },
    {
      key: "work",
      header: "Case work",
      render: (row) => <div><p className="text-sm font-semibold text-slate-700">{row.open_alerts} open</p><p className="mt-1 text-[11px] text-slate-500">{row.new_alerts} new · {row.open_alerts === 1 ? "1 work item" : `${row.open_alerts} work items`}</p></div>,
    },
    {
      key: "next",
      header: "Next step",
      render: (row) => <span className={row.needs_action ? "block max-w-[320px] text-sm leading-5 text-slate-700" : "block text-sm text-slate-500"}>{getRecommendedAction(row)}</span>,
    },
    {
      key: "action",
      header: "",
      render: (row) => (
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Link to={`/mentor/student/${row.student_id}`} className="ui-button ui-button-secondary !min-h-9 !px-3 !text-xs"><Icon name="open" />Open case</Link>
          {row.primary_alert && row.needs_action ? <ActionButton variant="primary" className="!min-h-9 !px-3 !text-xs" onClick={() => setSelectedAlert(row.primary_alert!)}>Intervene</ActionButton> : null}
          <ActionButton variant="secondary" className="!min-h-9 !px-3 !text-xs" disabled={completingAlertId === row.student_id || completedStudents.has(row.student_id) || Boolean(row.case_completed)} onClick={() => setCompletionTarget(row)}>
            {completingAlertId === row.student_id ? "Completing…" : (completedStudents.has(row.student_id) || row.case_completed) ? "Completed ✓" : "Mark as complete"}
          </ActionButton>
        </div>
      ),
    },
  ];

  return (
    <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle="Mentor workspace · academic support cases">
      <div className="space-y-7">
        <WorkspaceIntro role="mentor" name={user?.name} context="CSE · Semester 5 · 2026–27" />

        {error ? <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div> : null}

        <section aria-labelledby="mentor-metrics-title" className="space-y-3">
          <SectionHeading eyebrow="Today at a glance" title="Start with the students who need attention" description="" />
          <h2 id="mentor-metrics-title" className="sr-only">Mentor workload summary</h2>
          <div className="grid min-w-0 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            <MetricCard icon="attention" label="Needs action" value={loading ? "" : workspace?.students_needing_action ?? 0} detail="Unique students requiring a decision" tone="brand" loading={loading} />
            <MetricCard icon="critical" label="Critical students" value={loading ? "" : workspace?.critical_students ?? 0} detail="Students with at least one critical signal" tone="critical" loading={loading} />
            <MetricCard icon="attention" label="High-risk students" value={loading ? "" : workspace?.high_risk_students ?? 0} detail="Students at high or critical risk" tone="attention" loading={loading} />
            <MetricCard icon="alerts" label="Open case work" value={loading ? "" : workspace?.open_alerts ?? 0} detail={loading ? "Active work items" : `${workspace?.open_alert_students ?? 0} students represented`} tone="brand" loading={loading} />
            <MetricCard icon="students" label="Assigned students" value={loading ? "" : workspace?.assigned_students ?? 0} detail="Students in your assigned sections" loading={loading} />
            <MetricCard icon="alerts" label="Completed cases" value={loading ? "" : workspace?.completed_cases ?? 0} detail="Cases resolved and saved" tone="brand" loading={loading} />
          </div>
        </section>

        <Card id="mentor-queue" as="section" className="min-w-0 overflow-hidden" style={{ scrollMarginTop: "120px" }}>
          <div className="border-b border-slate-100 px-5 py-4 md:px-6">
            <SectionHeading eyebrow="Attention queue" title={filterLabel} description="Review a case to see why it needs attention and decide the next step." action={<span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[11px] font-semibold text-slate-600">{loading ? "Loading" : `${rows.length} shown`}</span>} />
          </div>
          <div className="border-b border-slate-100 bg-[#fbfdff] px-5 py-4 md:px-6">
            <div className="u8-filter-grid grid min-w-0 gap-3 lg:grid-cols-[minmax(0,1fr)_210px_170px_auto] lg:items-end">
              <label className="grid min-w-0 gap-1.5 text-xs font-semibold text-slate-600">Find a student<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name or roll number" className="ui-control w-full" /></label>
              <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Risk type<select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)} className="ui-control"><option value="all">All risk types</option><option value="course_failure">Course failure</option><option value="backlog">Backlog</option><option value="gpa_threshold">GPA threshold</option><option value="attendance_shortage">Attendance shortage</option><option value="support_attention">Support attention</option></select></label>
              <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Risk level<select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)} className="ui-control"><option value="all">All levels</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="MODERATE">Moderate</option><option value="LOW">Low</option></select></label>
              <label className="inline-flex min-h-[42px] items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700"><input type="checkbox" checked={actionOnly} onChange={(event) => setActionOnly(event.target.checked)} className="h-4 w-4 accent-[#2767bf]" /> Needs action only</label>
            </div>
          </div>
          <div className="p-3 md:p-5">
            {loading ? (
              <div className="space-y-2" aria-busy="true">
                {[1, 2, 3, 4, 5].map((item) => <div key={item} className="grid grid-cols-1 gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-4 md:grid-cols-[1.2fr_.9fr_.6fr_.6fr_.75fr_1.4fr_.8fr]"><div className="h-12 animate-pulse rounded bg-white" /><div className="h-12 animate-pulse rounded bg-white" /><div className="h-12 animate-pulse rounded bg-white" /><div className="h-12 animate-pulse rounded bg-white" /><div className="h-12 animate-pulse rounded bg-white" /><div className="h-12 animate-pulse rounded bg-white" /><div className="h-12 animate-pulse rounded bg-white" /></div>)}
              </div>
            ) : (
              <>
                <Table columns={columns} rows={rows} rowKey={(row) => row.student_id} caption="Mentor student attention queue" emptyMessage="No students match the current filters." />
                {!loading && (workspace?.total_pages ?? 1) > 1 ? <div className="mt-4 flex items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500"><span>Page {workspace?.page ?? page} of {workspace?.total_pages ?? 1} · {workspace?.total_students ?? rows.length} students</span><div className="flex gap-2"><button type="button" className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold disabled:opacity-40" disabled={page <= 1} onClick={()=>setPage(p=>Math.max(1,p-1))}>Previous</button><button type="button" className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold disabled:opacity-40" disabled={page >= (workspace?.total_pages ?? 1)} onClick={()=>setPage(p=>p+1)}>Next</button></div></div> : null}
              </>
            )}
          </div>
        </Card>

        {selectedAlert ? (
          <Card as="section" className="border-brand-200 bg-[#f8fbff] p-5 md:p-6">
            <SectionHeading eyebrow="Support action" title={`${selectedAlert.student_name} · ${readableRiskType(selectedAlert.risk_type)}`} description="Record the support action and follow-up." action={<div className="flex flex-wrap items-center justify-end gap-2">{selectedAlert.status === "NEW" ? <ActionButton variant="secondary" className="!min-h-9 !px-3 !text-xs" onClick={() => void handleAcknowledge(selectedAlert.alert_id)}>Acknowledge</ActionButton> : null}<ActionButton variant="ghost" className="!min-h-9 !px-2 !text-xs" onClick={() => setSelectedAlert(null)}>Close</ActionButton></div>} />
            <form onSubmit={(event) => void handleIntervention(event)} className="mt-4 grid min-w-0 gap-4 lg:grid-cols-[180px_180px_minmax(0,1fr)_auto] lg:items-end">
              <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Next status<select value={interventionStatus} onChange={(event) => setInterventionStatus(event.target.value as typeof interventionStatus)} className="ui-control"><option value="ACKNOWLEDGED">Acknowledged</option><option value="ACTION_TAKEN">Action taken</option><option value="FOLLOW_UP">Follow-up</option><option value="RESOLVED">Resolved</option></select></label>
              <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Follow-up date<input required={interventionStatus === "FOLLOW_UP"} type="date" min={new Date().toISOString().slice(0, 10)} value={followUpDate} onChange={(event) => setFollowUpDate(event.target.value)} className="ui-control" /></label>
              <label className="grid gap-1.5 text-xs font-semibold text-slate-600">What did you do?<textarea required value={interventionNotes} onChange={(event) => setInterventionNotes(event.target.value)} placeholder="Record the support action, agreement or follow-up plan." className="min-h-[84px] min-w-0 rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-ink-900" /></label>
              <ActionButton type="submit" disabled={savingIntervention || !interventionNotes.trim()} variant="primary">Save action</ActionButton>
            </form>
          </Card>
        ) : null}
      </div>
      <CompleteCaseDialog open={Boolean(completionTarget)} studentName={completionTarget?.student_name ?? "student"} saving={Boolean(completingAlertId)} onClose={() => setCompletionTarget(null)} onConfirm={(payload) => completionTarget && void handleMarkComplete(completionTarget, payload)} />
    </InstitutionalShell>
  );
}
