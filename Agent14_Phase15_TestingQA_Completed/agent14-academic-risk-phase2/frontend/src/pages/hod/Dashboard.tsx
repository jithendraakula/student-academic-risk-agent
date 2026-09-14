import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../../components/Card";
import MetricSkeleton from "../../components/MetricSkeleton";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import Table, { type TableColumn } from "../../components/Table";
import { useAuth } from "../../context/AuthContext";
import InstitutionalAIPanel from "../../components/InstitutionalAIPanel";
import { getHodSummary, getMentorComparison, getMentorStudents, getRiskOverview, type HodSummary, type MentorComparisonRow, type MentorStudent, type RiskOverviewRow } from "../../features/hod/api";
import { readableRiskType } from "../../features/mentor/formatters";
import { subscribeToCaseWorkUpdates, subscribeToLiveCaseWorkUpdates } from "../../features/caseWorkEvents";

function Metric({ label, value, detail, tone = "text-ink-900", loading = false }: { label: string; value: number | string; detail: string; tone?: string; loading?: boolean }) {
  if (loading) return <Card><MetricSkeleton label={label} /></Card>;
  return <Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">{label}</p><p className={`mt-2 text-3xl font-bold tracking-tight ${tone}`}>{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></Card>;
}

function RiskOverview({ items }: { items: RiskOverviewRow[] }) {
  return <Card as="section" className="min-w-0 p-0"><div className="border-b border-slate-100 px-5 py-4"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Department risk profile</p><h2 className="mt-1 text-lg font-bold text-ink-900">Affected students by risk type</h2><p className="mt-1 text-xs text-slate-500">Unique students with elevated risk. One student may have more than one risk signal.</p></div><div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-5">{items.map((item) => <div key={item.risk_type} className="rounded-xl border border-slate-100 bg-slate-50/60 p-4"><p className="text-xs font-semibold text-slate-500">{item.risk_label}</p><div className="mt-2 flex items-end justify-between"><span className="text-2xl font-bold text-ink-900">{item.affected_students}</span><span className="text-xs font-semibold text-brand-700">{item.affected_rate}%</span></div><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-brand-500" style={{ width: `${Math.min(100, item.affected_rate)}%` }} /></div><p className="mt-2 text-[11px] text-slate-400">Avg priority {Math.round(item.average_priority)} pts</p></div>)}</div></Card>;
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
  const [mentorSections, setMentorSections] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDepartmentOverview() {
    try {
      const [summaryData, comparison, risks] = await Promise.all([getHodSummary(), getMentorComparison(), getRiskOverview()]);
      setSummary(summaryData);
      setMentors(comparison.items);
      setRiskOverview(risks.items);
      setError(null);
    } catch {
      setError("The department overview could not be loaded. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDepartmentOverview();
    const stop = subscribeToCaseWorkUpdates(() => void loadDepartmentOverview());
    const stopLive = subscribeToLiveCaseWorkUpdates(() => void loadDepartmentOverview());
    const timer = window.setInterval(() => void loadDepartmentOverview(), 15000);
    return () => { stop(); stopLive(); window.clearInterval(timer); };
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
      .then((result) => { setSelectedMentorName(result.mentor_name); setMentorStudents(result.items); setMentorSections(result.sections ?? Array.from(new Set(result.items.map((item) => item.section))).sort()); })
      .catch(() => setError("The selected mentor's students could not be loaded."))
      .finally(() => setStudentsLoading(false));
  }, [selectedMentor, search, section, riskType, needsAction]);

  function selectMentor(mentorId: string) {
    const isDeselecting = selectedMentor === mentorId;
    setSelectedMentor(isDeselecting ? null : mentorId);
    if (isDeselecting) {
      setMentorStudents([]);
      setMentorSections([]);
      return;
    }
    setSection("ALL");
    setRiskType("ALL");
    setNeedsAction("ALL");
    setSearch("");
    window.requestAnimationFrame(() => {
      document.getElementById("hod-mentor-students")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  const mentorColumns: TableColumn<MentorComparisonRow>[] = [
    { key: "mentor", header: "Mentor", render: (mentor) => <button type="button" onClick={() => selectMentor(mentor.mentor_id)} className="text-left font-semibold text-ink-900 hover:text-brand-600">{mentor.mentor_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{mentor.sections?.join(" · ") || "Assigned sections"}</span></button> },
    { key: "assigned", header: "Students", render: (mentor) => mentor.assigned_students },
    { key: "critical", header: "Critical", render: (mentor) => <span className="font-semibold text-red-700">{mentor.critical_students}</span> },
    { key: "high", header: "High+critical", render: (mentor) => <span className="font-semibold text-orange-700">{mentor.high_risk_students}</span> },
    { key: "action", header: "Need action", render: (mentor) => <span className="font-semibold text-brand-700">{mentor.students_needing_action}</span> },
    { key: "alerts", header: "Open work", render: (mentor) => <span><strong>{mentor.open_alerts}</strong><span className="ml-1 text-[10px] text-slate-400">items</span></span> },
    { key: "load", header: "Priority load", render: (mentor) => <span className="font-semibold text-brand-700">{Math.round(mentor.intervention_load)} pts</span> },
    { key: "rate", header: "Action rate", render: (mentor) => `${Math.round(mentor.action_rate)}%` },
  ];

  const studentColumns: TableColumn<MentorStudent>[] = [
    { key: "student", header: "Student", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-ink-900 hover:text-brand-600">{student.student_name}<span className="mt-0.5 block text-xs font-normal text-slate-400">{student.roll_number ?? student.student_id}</span></Link> },
    { key: "batch", header: "Batch", render: (student) => student.batch },
    { key: "section", header: "Section", render: (student) => student.section },
    { key: "risk", header: "Risk", render: (student) => <span className={student.critical ? "font-semibold text-red-700" : student.high_risk ? "font-semibold text-orange-700" : "text-slate-500"}>{student.critical ? "Critical" : student.high_risk ? "High risk" : "Stable"}</span> },
    { key: "primary", header: "Risk(s)", render: (student) => <div className="flex min-w-0 flex-wrap gap-1.5">{(student.risk_breakdown ?? []).map((risk) => <span key={`${risk.risk_type}-${risk.course_ids.join("-")}`} title={`${risk.risk_label} · ${risk.risk_level}`} className="rounded-full border border-slate-200 bg-white px-2 py-1 text-[10px] font-bold text-slate-700">{risk.risk_label}{risk.course_ids.length ? ` · ${risk.course_ids.join(", ")}` : ""}</span>)}{!(student.risk_breakdown ?? []).length ? "—" : null}</div> },
    { key: "priority", header: "Priority", render: (student) => <span className="font-semibold text-brand-700">{Math.round(student.priority_score)} pts</span> },
    { key: "alerts", header: "Open case work", render: (student) => student.open_alerts },
    { key: "action", header: "Profile", render: (student) => <Link to={`/mentor/student/${student.student_id}`} className="font-semibold text-brand-600 hover:text-brand-700">Open</Link> },
  ];

  const pageDepartment = summary?.department ?? user?.department ?? "";
  return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle={`HOD Workspace · ${pageDepartment || "CSE Department"} · Faculty support oversight`}>
    <div className="space-y-6">
      <WorkspaceIntro role="hod" name={user?.name} context="CSE · Semester 5 · 2026–27" />
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <section className="grid min-w-0 gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Department summary">
        <Metric label="Students monitored" value={summary?.total_students ?? "—"} detail="Students in CSE" />
        <Metric label="Critical students" value={summary?.critical_students ?? "—"} detail="Unique students" tone="text-red-700" />
        <Metric label="Needs action" value={summary?.students_needing_action ?? "—"} detail="Unique students" tone="text-orange-700" />
        <Metric label="Open case work" value={summary?.open_alerts ?? "—"} detail={`${summary?.open_alert_students ?? 0} students represented`} />
        <Metric label="Completed cases" value={summary?.completed_cases ?? "—"} detail="Persisted case completions" tone="text-emerald-700" />
        <Metric label="Priority load" value={summary ? `${Math.round(summary.intervention_load)} pts` : "—"} detail="Priority across active case work" tone="text-brand-700" />
      </section>

      <Card as="section" className="min-w-0 p-0">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div><p className="ui-eyebrow">Mentor oversight</p><h2 className="mt-1 text-lg font-bold text-ink-900">Where does mentor support demand sit?</h2><p className="mt-1 text-xs leading-5 text-slate-500">Students are counted once; open work counts active case items.</p></div>
          
        </div>
        <div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading mentor support overview...</p> : <Table columns={mentorColumns} rows={mentors} rowKey={(mentor) => mentor.mentor_id} caption="Department mentor comparison" emptyMessage="No mentors found in this department." />}</div>
      </Card>

      <section id="hod-mentor-students" className="scroll-mt-28">
      <Card as="section" className="min-w-0 p-0">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div><p className="ui-eyebrow">Student review</p><h2 className="mt-1 text-lg font-bold text-ink-900">{selectedMentor ? `Students assigned to ${selectedMentorName}` : "Select a mentor to review students"}</h2><p className="mt-1 text-xs text-slate-500">Use the filters to move from department oversight to one student case.</p></div>
          {selectedMentor ? <div className="flex flex-wrap items-center gap-2"><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search student" className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" /><select value={section} onChange={(e) => setSection(e.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="ALL">All sections</option>{mentorSections.map((item) => <option key={item} value={item}>{item}</option>)}</select><select value={riskType} onChange={(e) => setRiskType(e.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="ALL">All risks</option><option value="attendance_shortage">Attendance</option><option value="course_failure">Course failure</option><option value="backlog">Backlog</option><option value="gpa_threshold">GPA</option><option value="support_attention">Support attention</option></select><select value={needsAction} onChange={(e) => setNeedsAction(e.target.value)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"><option value="ALL">All students</option><option value="YES">Needs action</option><option value="NO">Monitor</option></select></div> : null}
        </div>
        <div className="p-3 md:p-5">{studentsLoading ? <p className="px-2 py-8 text-sm text-slate-500">Loading assigned students...</p> : <Table columns={studentColumns} rows={mentorStudents} rowKey={(student) => student.student_id} caption="Mentor assigned student drill-down" emptyMessage={selectedMentor ? "No students match the current filters." : "Choose a mentor above to open their students."} />}</div>
      </Card>
      </section>

      {!loading && riskOverview.length ? <RiskOverview items={riskOverview} /> : null}

      <InstitutionalAIPanel role="hod" />
    </div>
  </InstitutionalShell>;
}
