import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import MetricSkeleton from "../../components/MetricSkeleton";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import { subscribeToCaseWorkUpdates, subscribeToLiveCaseWorkUpdates } from "../../features/caseWorkEvents";
import InstitutionalAIPanel from "../../components/InstitutionalAIPanel";
import {
  getDeanSummary,
  getDepartmentComparison,
  getDepartmentStudents,
  getPriorityQueue,
  getRiskHeatmap,
  type DeanStudent,
  type DeanSummary,
  type DepartmentComparisonRow,
  type PriorityQueueRow,
  type RiskHeatmapRow,
} from "../../features/dean/api";

function Metric({ label, value, detail, tone = "text-ink-900", loading = false }: { label: string; value: number | string; detail: string; tone?: string; loading?: boolean }) {
  if (loading) return <Card><MetricSkeleton label={label} /></Card>;
  return <Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p><p className={`mt-2 text-3xl font-bold tracking-tight ${tone}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></Card>;
}

function heatTone(value: number) {
  if (value >= 75) return "bg-red-100 text-red-800";
  if (value >= 50) return "bg-orange-100 text-orange-800";
  if (value >= 25) return "bg-amber-100 text-amber-800";
  return "bg-green-100 text-green-800";
}

function riskLabel(value: string | null) {
  const labels: Record<string, string> = {
    attendance_shortage: "Attendance shortage",
    course_failure: "Course failure",
    backlog: "Backlog",
    gpa_threshold: "GPA threshold",
    discontinuation: "Support attention",
    support_attention: "Support attention",
  };
  return value ? labels[value] ?? value : "—";
}

export default function DeanDashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<DeanSummary | null>(null);
  const [departments, setDepartments] = useState<DepartmentComparisonRow[]>([]);
  const [heatmap, setHeatmap] = useState<RiskHeatmapRow[]>([]);
  const [queue, setQueue] = useState<PriorityQueueRow[]>([]);
  const [students, setStudents] = useState<DeanStudent[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState<string | null>(null);
  const [selectedDepartmentName, setSelectedDepartmentName] = useState("");
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadInstitutionOverview() {
    try {
      const [institution, comparison, riskRows, priorityRows] = await Promise.all([getDeanSummary(), getDepartmentComparison(), getRiskHeatmap(), getPriorityQueue()]);
      setSummary(institution);
      setDepartments(comparison);
      setHeatmap(riskRows);
      setQueue(priorityRows.items);
      setError(null);
    } catch {
      setError("The institution overview could not be loaded. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadInstitutionOverview();
    const stop = subscribeToCaseWorkUpdates(() => void loadInstitutionOverview());
    const stopLive = subscribeToLiveCaseWorkUpdates(() => void loadInstitutionOverview());
    const timer = window.setInterval(() => void loadInstitutionOverview(), 15000);
    return () => { stop(); stopLive(); window.clearInterval(timer); };
  }, []);

  useEffect(() => {
    if (!selectedDepartment) return;
    getDepartmentStudents(selectedDepartment)
      .then((result) => { setSelectedDepartmentName(result.department); setStudents(result.items); })
      .catch(() => setError("The selected department students could not be loaded."))
      .finally(() => setStudentsLoading(false));
  }, [selectedDepartment]);

  function selectDepartment(department: string) {
    setSelectedDepartment((current) => current === department ? null : department);
    if (selectedDepartment === department) setStudents([]);
    else setStudentsLoading(true);
  }

  const comparisonColumns: TableColumn<DepartmentComparisonRow>[] = [
    { key: "department", header: "Department", render: (row) => <button type="button" onClick={() => selectDepartment(row.department)} className="text-left font-semibold text-ink-900 hover:text-brand-600">{row.department}<span className="mt-0.5 block text-xs font-normal text-slate-400">Open department</span></button> },
    { key: "students", header: "Students", render: (row) => row.total_students },
    { key: "critical", header: "Critical", render: (row) => <span className="font-semibold text-red-700">{row.critical_students}</span> },
    { key: "high", header: "High risk", render: (row) => <span className="font-semibold text-orange-700">{row.high_risk_students}</span> },
    { key: "action", header: "Needs action", render: (row) => <span className="font-semibold text-brand-700">{row.students_needing_action}</span> },
    { key: "priority", header: "Avg. priority", render: (row) => <span className="font-semibold text-brand-700">{Math.round(row.average_priority)} pts</span> },
    { key: "coverage", header: "Open case work", render: (row) => <span>{row.active_interventions}</span> },
  ];

  const heatmapColumns: TableColumn<RiskHeatmapRow>[] = [
    { key: "department", header: "Department", render: (row) => <span className="font-semibold text-ink-900">{row.department}</span> },
    { key: "attendance", header: "Attendance", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.attendance_shortage)}`}>{row.attendance_shortage}%</span> },
    { key: "course", header: "Course failure", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.course_failure)}`}>{row.course_failure}%</span> },
    { key: "backlog", header: "Backlog", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.backlog)}`}>{row.backlog}%</span> },
    { key: "gpa", header: "GPA threshold", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.gpa_threshold)}`}>{row.gpa_threshold}%</span> },
    { key: "support", header: "Support attention", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.discontinuation)}`}>{row.discontinuation}%</span> },
  ];

  const queueColumns: TableColumn<PriorityQueueRow>[] = [
    { key: "student", header: "Student", render: (row) => <Link to={`/mentor/student/${row.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{row.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{row.roll_number ?? row.student_id} · {row.department}</span></Link> },
    { key: "risk", header: "Primary risk", render: (row) => riskLabel(row.primary_risk) },
    { key: "level", header: "Level", render: (row) => <span className={`font-semibold ${row.risk_level === "CRITICAL" ? "text-red-700" : row.risk_level === "HIGH" ? "text-orange-700" : "text-brand-700"}`}>{row.risk_level}</span> },
    { key: "priority", header: "Priority", render: (row) => <span className="font-bold text-ink-900">{Math.round(row.priority_score)}</span> },
    { key: "action", header: "Action", render: (row) => <Link to={`/mentor/student/${row.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open</Link> },
  ];

  const studentColumns: TableColumn<DeanStudent>[] = [
    { key: "student", header: "Student", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{student.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{student.roll_number ?? student.student_id}</span></Link> },
    { key: "section", header: "Section", render: (student) => student.section },
    { key: "risk", header: "Risk(s)", render: (student) => <div className="flex min-w-0 flex-wrap gap-1.5">{(student.risk_breakdown ?? []).map((risk) => <span key={`${risk.risk_type}-${risk.course_ids.join("-")}`} title={`${risk.risk_label} · ${risk.risk_level}`} className="rounded-full border border-slate-200 bg-white px-2 py-1 text-[10px] font-bold text-slate-700">{risk.risk_label}{risk.course_ids.length ? ` · ${risk.course_ids.join(", ")}` : ""}</span>)}{!(student.risk_breakdown ?? []).length ? <span>{student.risk_level} · {riskLabel(student.primary_risk)}</span> : null}</div> },
    { key: "priority", header: "Priority", render: (student) => <span className="font-semibold">{Math.round(student.priority_score)}</span> },
    { key: "action", header: "Status", render: (student) => student.needs_action ? <span className="font-semibold text-orange-700">Needs action</span> : <span className="text-slate-500">Monitor</span> },
  ];

  return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle="Dean Workspace · Institution-wide academic support oversight">
    <div className="space-y-6">
      <WorkspaceIntro role="dean" name={user?.name} context="CSE · Semester 5 · 2026–27" />
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section className="grid min-w-0 gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Institution summary">
        <Metric label="Students monitored" value={summary?.total_students ?? "—"} detail="Students in CSE" />
        <Metric label="Critical students" value={summary?.critical_students ?? "—"} detail="Unique students" tone="text-red-700" />
        <Metric label="Needs action" value={summary?.students_needing_action ?? "—"} detail="Unique students" tone="text-orange-700" />
        <Metric label="Open case work" value={summary?.open_alerts ?? "—"} detail={`${summary?.open_alert_students ?? 0} students represented`} tone="text-brand-700" />
        <Metric label="Completed cases" value={summary?.completed_cases ?? "—"} detail="Persisted case completions" tone="text-emerald-700" />
        <Metric label="Avg priority" value={summary ? Math.round(summary.average_priority) : "—"} detail="Average current priority / 100" />
      </section>

      <Card as="section" className="min-w-0 p-0">
        <div className="border-b border-slate-100 px-5 py-4"><p className="ui-eyebrow">Priority queue</p><h2 className="mt-1 text-lg font-bold text-ink-900">Which students need the most immediate attention?</h2><p className="mt-1 text-xs text-slate-500">Each student appears once. Open case work remains a separate workload count.</p></div>
        <div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading priority queue...</p> : <Table columns={queueColumns} rows={queue} rowKey={(row) => row.student_id} caption="Dean priority queue" emptyMessage="No students currently meet the support action policy." />}</div>
      </Card>

      <Card as="section" className="min-w-0 p-0">
        <div className="border-b border-slate-100 px-5 py-4"><p className="ui-eyebrow">Department oversight</p><h2 className="mt-1 text-lg font-bold text-ink-900">Where is support demand concentrated?</h2><p className="mt-1 text-xs text-slate-500">Current institution scope: CSE.</p></div>
        <div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department comparison...</p> : <Table columns={comparisonColumns} rows={departments} rowKey={(row) => row.department} caption="Dean department comparison" emptyMessage="No departments found." />}</div>
      </Card>

      <Card as="section" className="min-w-0 p-0">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4"><div><p className="ui-eyebrow">Case review</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedDepartment ? `Students in ${selectedDepartmentName}` : "Select a department to review students"}</h2></div></div>
        <div className="p-3 md:p-5">{studentsLoading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department students...</p> : <Table columns={studentColumns} rows={students} rowKey={(student) => student.student_id} caption="Dean department student drill-down" emptyMessage={selectedDepartment ? "No students found in this department." : "Choose a department above to open its students."} />}</div>
      </Card>

      <div className="grid min-w-0 gap-6 xl:grid-cols-2">
        <Card as="section" className="min-w-0 p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Risk mix</p><h2 className="mt-1 text-lg font-bold text-ink-900">Current risk distribution</h2></div><div className="space-y-2 p-5">{summary?.risk_distribution.map((item) => <div key={item.risk_type} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-3"><div><p className="text-sm font-semibold text-ink-900">{item.risk_label}</p><p className="text-xs text-slate-500">{item.affected_students} students · {item.affected_rate}%</p></div><span className="text-sm font-bold text-brand-700">{Math.round(item.average_priority)}</span></div>)}</div></Card>
        <Card as="section" className="min-w-0 p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Risk concentration</p><h2 className="mt-1 text-lg font-bold text-ink-900">Risk by department</h2></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading risk concentration...</p> : <Table columns={heatmapColumns} rows={heatmap} rowKey={(row) => row.department} caption="Institutional risk concentration" />}</div></Card>
      </div>

      <InstitutionalAIPanel role="dean" />
    </div>
  </InstitutionalShell>;
}
