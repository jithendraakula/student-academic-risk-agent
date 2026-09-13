import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import InstitutionalAIPanel from "../../components/InstitutionalAIPanel";
import { getHodSummary, getMentorComparison, getMentorStudents, getRiskOverview, type HodSummary, type MentorComparisonRow, type MentorStudent, type RiskOverviewRow } from "../../features/hod/api";

function Metric({ label, value, detail, tone = "text-ink-900" }: { label: string; value: number | string; detail: string; tone?: string }) {
  return <Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p><p className={`mt-2 text-2xl font-bold tracking-tight ${tone}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></Card>;
}

function RiskOverview({ items }: { items: RiskOverviewRow[] }) {
  return <Card as="section" className="p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Department risk profile</p><h2 className="mt-1 text-lg font-bold text-ink-900">Affected students by risk type</h2><p className="mt-1 text-xs text-slate-500">One student is counted once per risk type. Support Attention remains a support-only signal.</p></div><div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-5">{items.map((item) => <div key={item.risk_type} className="rounded-xl border border-slate-100 bg-slate-50/60 p-4"><p className="text-xs font-semibold text-slate-500">{item.risk_label}</p><div className="mt-2 flex items-end justify-between"><span className="text-2xl font-bold text-ink-900">{item.affected_students}</span><span className="text-xs font-semibold text-brand-700">{item.affected_rate}%</span></div><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-brand-500" style={{ width: `${Math.min(100, item.affected_rate)}%` }} /></div><p className="mt-2 text-[11px] text-slate-400">Avg priority {Math.round(item.average_priority)} pts</p></div>)}</div></Card>;
}

export default function HodDashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<HodSummary | null>(null);
  const [mentors, setMentors] = useState<MentorComparisonRow[]>([]);
  const [riskOverview, setRiskOverview] = useState<RiskOverviewRow[]>([]);
  const [mentorStudents, setMentorStudents] = useState<MentorStudent[]>([]);
  const [selectedMentorName, setSelectedMentorName] = useState("");
  const [selectedMentor, setSelectedMentor] = useState<string | null>(null);
  const [section, setSection] = useState("ALL");
  const [riskType, setRiskType] = useState("ALL");
  const [needsAction, setNeedsAction] = useState("ALL");
  const [search, setSearch] = useState("");
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getHodSummary(), getMentorComparison(), getRiskOverview()])
      .then(([summaryData, comparison, risks]) => {
        setSummary(summaryData);
        setMentors(comparison.items);
        setRiskOverview(risks.items);
      })
      .catch(() => setError("The department overview could not be loaded. Check that the backend is running."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedMentor) return;
    setStudentsLoading(true);
    getMentorStudents(selectedMentor, {
      q: search || undefined,
      section: section === "ALL" ? undefined : section,
      risk_type: riskType === "ALL" ? undefined : riskType,
      needs_action: needsAction === "ALL" ? undefined : needsAction === "YES",
    })
      .then((result) => { setSelectedMentorName(result.mentor_name); setMentorStudents(result.items); })
      .catch(() => setError("The selected mentor's students could not be loaded."))
      .finally(() => setStudentsLoading(false));
  }, [selectedMentor, search, section, riskType, needsAction]);

  function selectMentor(mentorId: string) {
    setSelectedMentor((current) => current === mentorId ? null : mentorId);
    if (selectedMentor === mentorId) setMentorStudents([]);
    setSection("ALL"); setRiskType("ALL"); setNeedsAction("ALL"); setSearch("");
  }

  const mentorColumns: TableColumn<MentorComparisonRow>[] = [
    { key: "mentor", header: "Mentor", render: (mentor) => <button type="button" onClick={() => selectMentor(mentor.mentor_id)} className="text-left font-semibold text-ink-900 hover:text-brand-600">{mentor.mentor_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{mentor.mentor_id}</span></button> },
    { key: "assigned", header: "Assigned", render: (mentor) => mentor.assigned_students },
    { key: "critical", header: "Critical", render: (mentor) => <span className="font-semibold text-red-700">{mentor.critical_students}</span> },
    { key: "high", header: "High risk", render: (mentor) => <span className="font-semibold text-orange-700">{mentor.high_risk_students}</span> },
    { key: "action", header: "Needs action", render: (mentor) => <span className="font-semibold text-brand-700">{mentor.students_needing_action}</span> },
    { key: "alerts", header: "Open alerts", render: (mentor) => mentor.open_alerts },
    { key: "load", header: "Support load", render: (mentor) => <span className="font-semibold text-brand-700">{Math.round(mentor.intervention_load)} pts</span> },
    { key: "rate", header: "Action rate", render: (mentor) => `${Math.round(mentor.action_rate)}%` },
  ];

  const studentColumns: TableColumn<MentorStudent>[] = [
    { key: "student", header: "Student", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{student.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{student.student_id}</span></Link> },
    { key: "batch", header: "Batch", render: (student) => student.batch },
    { key: "section", header: "Section", render: (student) => student.section },
    { key: "risk", header: "Risk", render: (student) => <span className={student.critical ? "font-semibold text-red-700" : student.high_risk ? "font-semibold text-orange-700" : "text-slate-500"}>{student.critical ? "Critical" : student.high_risk ? "High risk" : "Stable"}</span> },
    { key: "primary", header: "Primary risk", render: (student) => student.primary_risk ?? "—" },
    { key: "priority", header: "Priority", render: (student) => <span className="font-semibold text-brand-700">{Math.round(student.priority_score)} pts</span> },
    { key: "alerts", header: "Open alerts", render: (student) => student.open_alerts },
    { key: "action", header: "Profile", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open</Link> },
  ];

  const pageDepartment = summary?.department ?? user?.department ?? "";
  return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle={`HOD Workspace · ${pageDepartment || "Department"} · Mentor workload and support oversight`}>
    <div className="space-y-6">
      <WorkspaceIntro role="hod" name={user?.name} context={pageDepartment} />
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Department summary">
        <Metric label="Students monitored" value={summary?.total_students ?? "—"} detail="Students in this department" />
        <Metric label="Critical students" value={summary?.critical_students ?? "—"} detail="Immediate support attention" tone="text-red-700" />
        <Metric label="Needs action" value={summary?.students_needing_action ?? "—"} detail="Canonical priority queue" tone="text-orange-700" />
        <Metric label="Open alerts" value={summary?.open_alerts ?? "—"} detail="Active mentor actions" />
        <Metric label="Support load" value={summary ? `${Math.round(summary.intervention_load)} pts` : "—"} detail="Aggregate active priority" tone="text-brand-700" />
      </section>
      {!loading && riskOverview.length ? <RiskOverview items={riskOverview} /> : null}
      <Card as="section" className="p-0"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Mentor oversight</p><h2 className="mt-1 text-lg font-bold text-ink-900">Support workload by mentor</h2></div><p className="text-xs text-slate-500">Workload indicates support demand, not teacher performance.</p></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department comparison...</p> : <Table columns={mentorColumns} rows={mentors} rowKey={(mentor) => mentor.mentor_id} caption="Department mentor comparison" emptyMessage="No mentors found in this department." />}</div></Card>
      <InstitutionalAIPanel role="hod" />
      <Card as="section" className="p-0"><div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 lg:flex-row lg:flex-wrap lg:items-end lg:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Mentor drill-down</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedMentor ? `Students assigned to ${selectedMentorName}` : "Select a mentor to view students"}</h2></div>{selectedMentor ? <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:flex-wrap sm:items-center lg:justify-end"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search student" className="col-span-2 min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm sm:col-auto sm:w-40" /><select value={section} onChange={(e) => setSection(e.target.value)} className="min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="ALL">All sections</option><option value="A">A</option><option value="B">B</option></select><select value={riskType} onChange={(e) => setRiskType(e.target.value)} className="min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="ALL">All risks</option><option value="attendance_shortage">Attendance</option><option value="course_failure">Course failure</option><option value="backlog">Backlog</option><option value="gpa_threshold">GPA</option><option value="discontinuation">Support attention</option></select><select value={needsAction} onChange={(e) => setNeedsAction(e.target.value)} className="min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="ALL">All students</option><option value="YES">Needs action</option><option value="NO">Stable</option></select></div> : null}</div><div className="p-3 md:p-5">{studentsLoading ? <p className="px-2 py-8 text-sm text-slate-500">Loading assigned students...</p> : <Table columns={studentColumns} rows={mentorStudents} rowKey={(student) => student.student_id} caption="Mentor assigned student drill-down" emptyMessage={selectedMentor ? "No students match the current filters." : "Click a mentor above to open their assigned students."} />}</div></Card>
    </div>
  </InstitutionalShell>;
}