import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import { getMentorComparison, getMentorStudents, type MentorComparisonRow, type MentorStudent } from "../../features/hod/api";

function Metric({ label, value, detail, tone = "text-ink-900" }: { label: string; value: number | string; detail: string; tone?: string }) {
  return <Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p><p className={`mt-2 text-3xl font-bold tracking-tight ${tone}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></Card>;
}

export default function HodDashboard() {
  const { user, logout } = useAuth();
  const [department, setDepartment] = useState(user?.department ?? "");
  const [mentors, setMentors] = useState<MentorComparisonRow[]>([]);
  const [mentorStudents, setMentorStudents] = useState<MentorStudent[]>([]);
  const [selectedMentorName, setSelectedMentorName] = useState("");
  const [selectedMentor, setSelectedMentor] = useState<string | null>(null);
  const [section, setSection] = useState("ALL");
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMentorComparison()
      .then((comparison) => { setDepartment(comparison.department); setMentors(comparison.items); })
      .catch(() => setError("The department overview could not be loaded. Check that the backend is running."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedMentor) return;
    getMentorStudents(selectedMentor)
      .then((result) => { setSelectedMentorName(result.mentor_name); setMentorStudents(result.items); })
      .catch(() => setError("The selected mentor's students could not be loaded."))
      .finally(() => setStudentsLoading(false));
  }, [selectedMentor]);

  function selectMentor(mentorId: string) {
    setSelectedMentor((current) => current === mentorId ? null : mentorId);
    if (selectedMentor === mentorId) {
      setMentorStudents([]);
      setStudentsLoading(false);
    } else {
      setStudentsLoading(true);
    }
    setSection("ALL");
  }

  const filteredStudents = mentorStudents.filter((student) => section === "ALL" || student.section === section);
  const totalAssigned = mentors.reduce((sum, mentor) => sum + mentor.assigned_students, 0);
  const openAlerts = mentors.reduce((sum, mentor) => sum + mentor.open_alerts, 0);
  const criticalStudents = mentors.reduce((sum, mentor) => sum + mentor.critical_students, 0);
  const interventionLoad = mentors.reduce((sum, mentor) => sum + mentor.intervention_load, 0);
  const mentorColumns: TableColumn<MentorComparisonRow>[] = [
    { key: "mentor", header: "Mentor", render: (mentor) => <button type="button" onClick={() => selectMentor(mentor.mentor_id)} className="text-left font-semibold text-ink-900 hover:text-brand-600">{mentor.mentor_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{mentor.mentor_id}</span></button> },
    { key: "assigned", header: "Assigned", render: (mentor) => mentor.assigned_students },
    { key: "critical", header: "Critical", render: (mentor) => <span className="font-semibold text-red-700">{mentor.critical_students}</span> },
    { key: "high", header: "High risk", render: (mentor) => <span className="font-semibold text-orange-700">{mentor.high_risk_students}</span> },
    { key: "open", header: "Open alerts", render: (mentor) => mentor.open_alerts },
    { key: "load", header: "Support load", render: (mentor) => <span className="font-semibold text-brand-700">{Math.round(mentor.intervention_load)} pts</span> },
  ];
  const studentColumns: TableColumn<MentorStudent>[] = [
    { key: "student", header: "Student", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{student.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{student.student_id}</span></Link> },
    { key: "batch", header: "Batch", render: (student) => student.batch },
    { key: "section", header: "Section", render: (student) => student.section },
    { key: "risk", header: "Risk", render: (student) => <span className={student.critical ? "font-semibold text-red-700" : student.high_risk ? "font-semibold text-orange-700" : "text-slate-500"}>{student.critical ? "Critical" : student.high_risk ? "High risk" : "Stable"}</span> },
    { key: "priority", header: "Priority", render: (student) => <span className="font-semibold text-brand-700">{Math.round(student.priority_score)} pts</span> },
    { key: "alerts", header: "Open alerts", render: (student) => student.open_alerts },
    { key: "action", header: "Drill-down", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open profile</Link> },
  ];

  return (
    <main className="min-h-screen bg-canvas">
      <header className="border-b border-slate-200 bg-white px-5 py-4 md:px-8"><div className="mx-auto flex max-w-7xl items-center justify-between gap-5"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-600">HOD workspace</p><h1 className="mt-1 text-2xl font-bold tracking-tight text-ink-900">Department intelligence</h1><p className="mt-1 text-sm text-slate-500">{department} · Mentor workload and student support oversight</p></div><button type="button" onClick={logout} className="text-sm font-semibold text-slate-500 hover:text-ink-900">Sign out</button></div></header>
      <div className="mx-auto max-w-7xl space-y-6 px-5 py-6 md:px-8">
        {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Department summary"><Metric label="Students monitored" value={totalAssigned} detail="Assigned across department mentors" /><Metric label="Critical students" value={criticalStudents} detail="Immediate support attention" tone="text-red-700" /><Metric label="Open alerts" value={openAlerts} detail="Across mentor queues" tone="text-orange-700" /><Metric label="Support load" value={`${Math.round(interventionLoad)} pts`} detail="Aggregate active priority" tone="text-brand-700" /></section>
        <Card as="section" className="p-0"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Mentor oversight</p><h2 className="mt-1 text-lg font-bold text-ink-900">Support workload by mentor</h2></div><p className="text-xs text-slate-500">Workload indicates support demand, not teacher performance.</p></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading department comparison...</p> : <Table columns={mentorColumns} rows={mentors} rowKey={(mentor) => mentor.mentor_id} caption="Department mentor comparison" emptyMessage="No mentors found in this department." />}</div></Card>
        <Card as="section" className="p-0"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Mentor drill-down</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedMentor ? `Students assigned to ${selectedMentorName}` : "Select a mentor to view students"}</h2></div>{selectedMentor ? <label className="flex items-center gap-2 text-xs font-semibold text-slate-500">Section<select value={section} onChange={(event) => setSection(event.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal text-ink-900"><option value="ALL">All sections</option><option value="A">A</option><option value="B">B</option></select></label> : null}</div><div className="p-3 md:p-5">{studentsLoading ? <p className="px-2 py-8 text-sm text-slate-500">Loading assigned students...</p> : <Table columns={studentColumns} rows={filteredStudents} rowKey={(student) => student.student_id} caption="Mentor assigned student drill-down" emptyMessage={selectedMentor ? "No students match this section." : "Click a mentor above to open their assigned students."} />}</div></Card>
      </div>
    </main>
  );
}
