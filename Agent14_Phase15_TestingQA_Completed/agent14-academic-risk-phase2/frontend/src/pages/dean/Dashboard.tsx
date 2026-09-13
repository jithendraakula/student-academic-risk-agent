import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
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

function Metric({ label, value, detail, tone = "text-ink-900" }: { label: string; value: number | string; detail: string; tone?: string }) {
  return <Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p><p className={`mt-2 text-2xl font-bold tracking-tight ${tone}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></Card>;
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

  useEffect(() => {
    Promise.all([getDeanSummary(), getDepartmentComparison(), getRiskHeatmap(), getPriorityQueue()])
      .then(([institution, comparison, riskRows, priorityRows]) => {
        setSummary(institution);
        setDepartments(comparison);
        setHeatmap(riskRows);
        setQueue(priorityRows.items);
      })
      .catch(() => setError("The institution overview could not be loaded. Check that the backend is running."))
      .finally(() => setLoading(false));
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
    { key: "department", header: "Department", render: (row) => <button type="button" onClick={() => selectDepartment(row.department)} className="text-left font-semibold text-ink-900 hover:text-brand-600">{row.department}<span className="mt-0.5 block text-xs font-normal text-slate-400">Click to drill down</span></button> },
    { key: "students", header: "Students", render: (row) => row.total_students },
    { key: "critical", header: "Critical", render: (row) => <span className="font-semibold text-red-700">{row.critical_students}</span> },
    { key: "high", header: "High risk", render: (row) => <span className="font-semibold text-orange-700">{row.high_risk_students}</span> },
    { key: "action", header: "Needs action", render: (row) => <span className="font-semibold text-brand-700">{row.students_needing_action}</span> },
    { key: "priority", header: "Avg priority", render: (row) => <span className="font-semibold text-brand-700">{Math.round(row.average_priority)} pts</span> },
    { key: "coverage", header: "Active alerts", render: (row) => <span>{row.active_interventions}</span> },
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
    { key: "student", header: "Student", render: (row) => <Link to={`/mentor/student/${row.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{row.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{row.student_id} · {row.department}</span></Link> },
    { key: "risk", header: "Primary risk", render: (row) => riskLabel(row.primary_risk) },
    { key: "level", header: "Level", render: (row) => <span className={`font-semibold ${row.risk_level === "CRITICAL" ? "text-red-700" : row.risk_level === "HIGH" ? "text-orange-700" : "text-brand-700"}`}>{row.risk_level}</span> },
    { key: "priority", header: "Priority", render: (row) => <span className="font-bold text-ink-900">{Math.round(row.priority_score)}</span> },
    { key: "action", header: "Action", render: (row) => <Link to={`/mentor/student/${row.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open</Link> },
  ];

  const studentColumns: TableColumn<DeanStudent>[] = [
    { key: "student", header: "Student", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{student.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{student.student_id}</span></Link> },
    { key: "section", header: "Section", render: (student) => student.section },
    { key: "risk", header: "Risk", render: (student) => <span>{student.risk_level} · {riskLabel(student.primary_risk)}</span> },
    { key: "priority", header: "Priority", render: (student) => <span className="font-semibold">{Math.round(student.priority_score)}</span> },
    { key: "action", header: "Status", render: (student) => student.needs_action ? <span className="font-semibold text-orange-700">Needs action</span> : <span className="text-slate-500">Monitor</span> },
  ];

  return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle="Dean Workspace · Institution intelligence, risk concentration, and intervention coverage">
    <div className="space-y-6">
      <WorkspaceIntro role="dean" name={user?.name} context={"College-wide monitoring"} />
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Institution summary">
        <Metric label="Students monitored" value={summary?.total_students ?? "—"} detail={`${summary?.departments ?? 0} departments`} />
        <Metric label="Critical students" value={summary?.critical_students ?? "—"} detail="Across the institution" tone="text-red-700" />
        <Metric label="Needs action" value={summary?.students_needing_action ?? "—"} detail="Canonical priority queue" tone="text-orange-700" />
        <Metric label="Open alerts" value={summary?.open_alerts ?? "—"} detail="Active alert projections" tone="text-brand-700" />
        <Metric label="Avg priority" value={summary ? Math.round(summary.average_priority) : "—"} detail="Current student priority" />
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Institutional priority queue</p><h2 className="mt-1 text-lg font-bold text-ink-900">Students needing the most immediate attention</h2></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading priority queue...</p> : <Table columns={queueColumns} rows={queue} rowKey={(row) => row.student_id} caption="Dean priority queue" emptyMessage="No students currently meet the canonical alert policy." />}</div></Card>
        <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Risk mix</p><h2 className="mt-1 text-lg font-bold text-ink-900">Current institution-wide risk distribution</h2></div><div className="space-y-2 p-5">{summary?.risk_distribution.map((item) => <div key={item.risk_type} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-3"><div><p className="text-sm font-semibold text-ink-900">{item.risk_label}</p><p className="text-xs text-slate-500">{item.affected_students} students · {item.affected_rate}%</p></div><span className="text-sm font-bold text-brand-700">{Math.round(item.average_priority)}</span></div>)}</div></Card>
      </div>

      <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Institutional risk heatmap</p><h2 className="mt-1 text-lg font-bold text-ink-900">Risk concentration by department</h2><p className="mt-1 text-xs text-slate-500">Percentage of department students currently at or above the canonical heatmap risk threshold.</p></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading risk heatmap...</p> : <Table columns={heatmapColumns} rows={heatmap} rowKey={(row) => row.department} caption="Institutional risk heatmap" />}</div></Card>

      <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Department comparison</p><h2 className="mt-1 text-lg font-bold text-ink-900">Where institutional support is needed</h2><p className="mt-1 text-xs text-slate-500">Counts and priority remain based on the same canonical student-risk engine used by mentor and HOD workspaces.</p></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department comparison...</p> : <Table columns={comparisonColumns} rows={departments} rowKey={(row) => row.department} caption="Dean department comparison" emptyMessage="No departments found." />}</div></Card>

      <InstitutionalAIPanel role="dean" />
      <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Authorized drill-down</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedDepartment ? `Students in ${selectedDepartmentName}` : "Select a department to view students"}</h2></div><div className="p-3 md:p-5">{studentsLoading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department students...</p> : <Table columns={studentColumns} rows={students} rowKey={(student) => student.student_id} caption="Dean department student drill-down" emptyMessage={selectedDepartment ? "No students found in this department." : "Click a department above to open its students."} />}</div></Card>
    </div>
  </InstitutionalShell>;
}