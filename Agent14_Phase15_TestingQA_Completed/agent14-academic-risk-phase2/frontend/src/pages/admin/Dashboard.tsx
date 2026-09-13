import { useEffect, useMemo, useState } from "react";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import Table, { type TableColumn } from "../../components/Table";
import { getAdminConfig, getAdminStudents, getAdminTeachers, updateAdminConfig, type AdminConfig, type AdminStudent, type AdminTeacher } from "../../features/admin/api";

export default function AdminDashboard() {
  
  const [students, setStudents] = useState<AdminStudent[]>([]);
  const [teachers, setTeachers] = useState<AdminTeacher[]>([]);
  const [config, setConfig] = useState<AdminConfig>({ gpa_threshold: 7, attendance_threshold: 75 });
  const [tab, setTab] = useState<"students" | "teachers">("students");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getAdminStudents(), getAdminTeachers(), getAdminConfig()])
      .then(([studentRows, teacherRows, settings]) => { setStudents(studentRows); setTeachers(teacherRows); setConfig(settings); })
      .catch(() => setError("The Admin console could not load its configuration and records."))
      .finally(() => setLoading(false));
  }, []);

  async function saveConfig(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setSaved(false);
    try { setConfig(await updateAdminConfig(config)); setSaved(true); } catch { setError("Threshold configuration could not be saved."); } finally { setSaving(false); }
  }

  const filteredStudents = useMemo(() => students.filter((student) => `${student.student_id} ${student.student_name} ${student.department}`.toLowerCase().includes(search.toLowerCase())), [students, search]);
  const filteredTeachers = useMemo(() => teachers.filter((teacher) => `${teacher.teacher_id} ${teacher.teacher_name} ${teacher.department ?? ""} ${teacher.role}`.toLowerCase().includes(search.toLowerCase())), [teachers, search]);
  const studentColumns: TableColumn<AdminStudent>[] = [
    { key: "student", header: "Student", render: (row) => <><span className="font-semibold text-ink-900">{row.student_name}</span><span className="mt-0.5 block text-xs text-slate-400">{row.student_id}</span></> },
    { key: "department", header: "Department", render: (row) => row.department },
    { key: "batch", header: "Batch", render: (row) => row.batch },
    { key: "section", header: "Section", render: (row) => row.section },
  ];
  const teacherColumns: TableColumn<AdminTeacher>[] = [
    { key: "teacher", header: "Teacher", render: (row) => <><span className="font-semibold text-ink-900">{row.teacher_name}</span><span className="mt-0.5 block text-xs text-slate-400">{row.teacher_id}</span></> },
    { key: "role", header: "Role", render: (row) => <span className="capitalize">{row.role}</span> },
    { key: "department", header: "Department", render: (row) => row.department ?? "Institution-wide" },
    { key: "email", header: "Email", render: (row) => row.email },
  ];

  return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle="Administration · Records, assignments, roles, and academic risk configuration">
    <div className="space-y-6">
      <WorkspaceIntro role="admin" context="Policy and records" />
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      <section className="grid gap-4 sm:grid-cols-3" aria-label="Admin summary"><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Students</p><p className="mt-2 text-3xl font-bold text-ink-900">{students.length}</p><p className="mt-1 text-xs text-slate-500">Managed student records</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Teachers</p><p className="mt-2 text-3xl font-bold text-ink-900">{teachers.length}</p><p className="mt-1 text-xs text-slate-500">Faculty and role records</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Departments</p><p className="mt-2 text-3xl font-bold text-ink-900">{new Set(students.map((student) => student.department)).size}</p><p className="mt-1 text-xs text-slate-500">Mapped academic units</p></Card></section>
      <Card as="section"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Academic configuration</p><h2 className="mt-1 text-lg font-bold text-ink-900">Risk thresholds</h2></div><p className="max-w-md text-xs text-slate-500">These settings are stored for future model runs and risk calculations.</p></div><form onSubmit={(event) => void saveConfig(event)} className="mt-5 grid gap-4 md:grid-cols-[220px_220px_auto] md:items-end"><label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">GPA threshold<input type="number" min="0" max="10" step="0.1" value={config.gpa_threshold} onChange={(event) => setConfig({ ...config, gpa_threshold: Number(event.target.value) })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-ink-900" /></label><label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Attendance threshold (%)<input type="number" min="0" max="100" step="0.5" value={config.attendance_threshold} onChange={(event) => setConfig({ ...config, attendance_threshold: Number(event.target.value) })} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-ink-900" /></label><button type="submit" disabled={saving} className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">{saving ? "Saving..." : saved ? "Saved" : "Save thresholds"}</button></form></Card>
      <Card as="section" className="p-0"><div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Reference records</p><h2 className="mt-1 text-lg font-bold text-ink-900">Students and teachers</h2></div><div className="flex items-center gap-3"><div className="flex rounded-lg border border-slate-200 bg-slate-50 p-1"><button type="button" onClick={() => setTab("students")} className={`rounded-md px-3 py-1.5 text-xs font-semibold ${tab === "students" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"}`}>Students</button><button type="button" onClick={() => setTab("teachers")} className={`rounded-md px-3 py-1.5 text-xs font-semibold ${tab === "teachers" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"}`}>Teachers</button></div><input aria-label="Search records" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search records" className="w-48 rounded-lg border border-slate-200 px-3 py-2 text-sm" /></div></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading records...</p> : tab === "students" ? <Table columns={studentColumns} rows={filteredStudents} rowKey={(row) => row.student_id} caption="Admin student records" emptyMessage="No matching students." /> : <Table columns={teacherColumns} rows={filteredTeachers} rowKey={(row) => row.teacher_id} caption="Admin teacher records" emptyMessage="No matching teachers." />}</div></Card>
    </div>
  </InstitutionalShell>;
}
