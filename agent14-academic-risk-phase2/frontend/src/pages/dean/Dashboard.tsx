import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import { getDepartmentComparison, getDepartmentStudents, getRiskHeatmap, type DepartmentComparisonRow, type DeanStudent, type RiskHeatmapRow } from "../../features/dean/api";

function Metric({ label, value, detail, tone = "text-ink-900" }: { label: string; value: number | string; detail: string; tone?: string }) {
  return <Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p><p className={`mt-2 text-3xl font-bold tracking-tight ${tone}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></Card>;
}

function heatTone(value: number) {
  if (value >= 75) return "bg-red-100 text-red-800";
  if (value >= 50) return "bg-orange-100 text-orange-800";
  if (value >= 25) return "bg-amber-100 text-amber-800";
  return "bg-green-100 text-green-800";
}

export default function DeanDashboard() {
  const { logout } = useAuth();
  const [departments, setDepartments] = useState<DepartmentComparisonRow[]>([]);
  const [heatmap, setHeatmap] = useState<RiskHeatmapRow[]>([]);
  const [students, setStudents] = useState<DeanStudent[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState<string | null>(null);
  const [selectedDepartmentName, setSelectedDepartmentName] = useState("");
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getDepartmentComparison(), getRiskHeatmap()])
      .then(([comparison, riskRows]) => { setDepartments(comparison); setHeatmap(riskRows); })
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

  const totalStudents = departments.reduce((sum, row) => sum + row.total_students, 0);
  const criticalStudents = departments.reduce((sum, row) => sum + row.critical_students, 0);
  const activeInterventions = departments.reduce((sum, row) => sum + row.active_interventions, 0);
  const resolvedInterventions = departments.reduce((sum, row) => sum + row.resolved_interventions, 0);
  const comparisonColumns: TableColumn<DepartmentComparisonRow>[] = [
    { key: "department", header: "Department", render: (row) => <button type="button" onClick={() => selectDepartment(row.department)} className="text-left font-semibold text-ink-900 hover:text-brand-600">{row.department}<span className="mt-0.5 block text-xs font-normal text-slate-400">Click to drill down</span></button> },
    { key: "students", header: "Students", render: (row) => row.total_students },
    { key: "critical", header: "Critical", render: (row) => <span className="font-semibold text-red-700">{row.critical_students}</span> },
    { key: "high", header: "High risk", render: (row) => <span className="font-semibold text-orange-700">{row.high_risk_students}</span> },
    { key: "priority", header: "Avg priority", render: (row) => <span className="font-semibold text-brand-700">{Math.round(row.average_priority)} pts</span> },
    { key: "coverage", header: "Interventions", render: (row) => <span>{row.active_interventions} active · {row.resolved_interventions} resolved</span> },
  ];
  const heatmapColumns: TableColumn<RiskHeatmapRow>[] = [
    { key: "department", header: "Department", render: (row) => <span className="font-semibold text-ink-900">{row.department}</span> },
    { key: "attendance", header: "Attendance", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.attendance_shortage)}`}>{row.attendance_shortage}%</span> },
    { key: "course", header: "Course failure", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.course_failure)}`}>{row.course_failure}%</span> },
    { key: "backlog", header: "Backlog", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.backlog)}`}>{row.backlog}%</span> },
    { key: "gpa", header: "GPA threshold", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.gpa_threshold)}`}>{row.gpa_threshold}%</span> },
    { key: "support", header: "Support attention", render: (row) => <span className={`rounded-md px-2 py-1 text-xs font-bold ${heatTone(row.discontinuation)}`}>{row.discontinuation}%</span> },
  ];
  const studentColumns: TableColumn<DeanStudent>[] = [
    { key: "student", header: "Student", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{student.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{student.student_id}</span></Link> },
    { key: "batch", header: "Batch", render: (student) => student.batch },
    { key: "section", header: "Section", render: (student) => student.section },
    { key: "action", header: "Drill-down", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open profile</Link> },
  ];

  return <main className="min-h-screen bg-canvas">
    <header className="border-b border-slate-200 bg-white px-5 py-4 md:px-8"><div className="mx-auto flex max-w-7xl items-center justify-between gap-5"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-600">Dean workspace</p><h1 className="mt-1 text-2xl font-bold tracking-tight text-ink-900">Institution intelligence</h1><p className="mt-1 text-sm text-slate-500">College-wide risk patterns and intervention coverage</p></div><button type="button" onClick={logout} className="text-sm font-semibold text-slate-500 hover:text-ink-900">Sign out</button></div></header>
    <div className="mx-auto max-w-7xl space-y-6 px-5 py-6 md:px-8">
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Institution summary"><Metric label="Students monitored" value={totalStudents} detail={`${departments.length} departments`} /><Metric label="Critical students" value={criticalStudents} detail="Across the institution" tone="text-red-700" /><Metric label="Active interventions" value={activeInterventions} detail="Currently requiring action" tone="text-orange-700" /><Metric label="Resolved interventions" value={resolvedInterventions} detail="Recorded outcomes" tone="text-green-700" /></section>
      <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Institutional risk heatmap</p><h2 className="mt-1 text-lg font-bold text-ink-900">Risk concentration by department</h2><p className="mt-1 text-xs text-slate-500">Percentage of department students or course records currently flagged at high risk or above.</p></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading risk heatmap...</p> : <Table columns={heatmapColumns} rows={heatmap} rowKey={(row) => row.department} caption="Institutional risk heatmap" />}</div></Card>
      <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Department comparison</p><h2 className="mt-1 text-lg font-bold text-ink-900">Where institutional support is needed</h2></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department comparison...</p> : <Table columns={comparisonColumns} rows={departments} rowKey={(row) => row.department} caption="Dean department comparison" emptyMessage="No departments found." />}</div></Card>
      <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Authorized drill-down</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedDepartment ? `Students in ${selectedDepartmentName}` : "Select a department to view students"}</h2></div><div className="p-3 md:p-5">{studentsLoading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department students...</p> : <Table columns={studentColumns} rows={students} rowKey={(student) => student.student_id} caption="Dean department student drill-down" emptyMessage={selectedDepartment ? "No students found in this department." : "Click a department above to open its students."} />}</div></Card>
    </div>
  </main>;
}
