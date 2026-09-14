import { useEffect, useState } from "react";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import WorkspaceIntro from "../../components/WorkspaceIntro";
import Table, { type TableColumn } from "../../components/Table";
import { getAdminCaseSummary, getAdminConfig, getAdminStudents, getAdminTeachers, updateAdminConfig, getAdminAuditLogs, type AdminCaseSummary, type AdminConfig, type AdminStudent, type AdminTeacher, type AdminAuditLog } from "../../features/admin/api";
import { subscribeToCaseWorkUpdates, subscribeToLiveCaseWorkUpdates } from "../../features/caseWorkEvents";

const PAGE_SIZE = 50;

function Pagination({ page, totalPages, totalRows, onPageChange }: { page: number; totalPages: number; totalRows: number; onPageChange: (next: number) => void }) {
  if (totalRows <= PAGE_SIZE) return null;
  const start = (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, totalRows);
  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500" aria-label="Pagination">
      <span>Showing {start}–{end} of {totalRows}</span>
      <div className="flex items-center gap-2">
        <button type="button" onClick={() => onPageChange(Math.max(1, page - 1))} disabled={page === 1} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold disabled:cursor-not-allowed disabled:opacity-40">Previous</button>
        <span className="min-w-16 text-center font-semibold text-slate-600">Page {page} / {totalPages}</span>
        <button type="button" onClick={() => onPageChange(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="rounded-lg border border-slate-200 px-3 py-1.5 font-semibold disabled:cursor-not-allowed disabled:opacity-40">Next</button>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [students, setStudents] = useState<AdminStudent[]>([]);
  const [teachers, setTeachers] = useState<AdminTeacher[]>([]);
  const [studentTotal, setStudentTotal] = useState(0);
  const [teacherTotal, setTeacherTotal] = useState(0);
  const [config, setConfig] = useState<AdminConfig>({ gpa_threshold: 7, attendance_threshold: 75 });
  const [caseSummary, setCaseSummary] = useState<AdminCaseSummary | null>(null);
  const [tab, setTab] = useState<"students" | "teachers" | "audit">("students");
  const [audit, setAudit] = useState<AdminAuditLog[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [auditPage, setAuditPage] = useState(1);
  const [auditTotal, setAuditTotal] = useState(0);
  const AUDIT_PAGE_SIZE = 25;

  async function loadAdminData() {
    try {
      const [studentRows, teacherRows, settings, cases, auditRows] = await Promise.all([getAdminStudents({ q: search || undefined, page, page_size: PAGE_SIZE }), getAdminTeachers({ q: search || undefined, page, page_size: PAGE_SIZE }), getAdminConfig(), getAdminCaseSummary(), getAdminAuditLogs({ q: search || undefined, page: auditPage, page_size: AUDIT_PAGE_SIZE })]);
      setStudents(studentRows.items); setTeachers(teacherRows.items); setStudentTotal(studentRows.total); setTeacherTotal(teacherRows.total); setConfig(settings); setCaseSummary(cases); setAudit(auditRows.items); setAuditTotal(auditRows.total); setError(null);
    } catch { setError("The Admin console could not load its configuration and records."); }
    finally { setLoading(false); }
  }

  useEffect(() => {
    void loadAdminData();
    const stop = subscribeToCaseWorkUpdates(() => void loadAdminData());
    const stopLive = subscribeToLiveCaseWorkUpdates(() => void loadAdminData());
    const timer = window.setInterval(() => void loadAdminData(), 15000);
    return () => { stop(); stopLive(); window.clearInterval(timer); };
  }, [page, auditPage, search]);

  async function saveConfig(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setSaved(false);
    setError(null);
    try { setConfig(await updateAdminConfig(config)); setSaved(true); } catch { setError("Threshold configuration could not be saved."); } finally { setSaving(false); }
  }

  useEffect(() => { setPage(1); setAuditPage(1); }, [tab, search]);

  const totalPages = Math.max(1, Math.ceil((tab === "students" ? studentTotal : teacherTotal) / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pagedStudents = students;
  const pagedTeachers = teachers;

  const studentColumns: TableColumn<AdminStudent>[] = [
    { key: "student", header: "Student", render: (row) => <><span className="block break-words font-semibold text-ink-900">{row.student_name}</span><span className="mt-0.5 block text-xs text-slate-400">{row.roll_number ?? row.student_id}</span></> },
    { key: "department", header: "Department", render: (row) => row.department },
    { key: "batch", header: "Batch", render: (row) => row.batch },
    { key: "section", header: "Section", render: (row) => row.section },
  ];
  const teacherColumns: TableColumn<AdminTeacher>[] = [
    { key: "teacher", header: "Teacher", render: (row) => <><span className="block break-words font-semibold text-ink-900">{row.teacher_name}</span><span className="mt-0.5 block text-xs text-slate-400">{row.teacher_id}</span></> },
    { key: "role", header: "Role", render: (row) => <span className="capitalize">{row.role}</span> },
    { key: "department", header: "Department", render: (row) => row.department ?? "Institution-wide" },
    { key: "email", header: "Email", render: (row) => <span className="break-all">{row.email}</span> },
  ];

  return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC RISK MANAGEMENT" subtitle="Administration · Records, assignments, roles, and academic risk configuration">
    <div className="space-y-6">
      <WorkspaceIntro role="admin" context="Policy and records" />
      {error ? <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}
      <section className="grid min-w-0 gap-4 sm:grid-cols-2 xl:grid-cols-5" aria-label="Admin summary"><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Students</p><p className="mt-2 text-3xl font-bold text-ink-900">{loading ? "—" : studentTotal}</p><p className="mt-1 text-xs text-slate-500">Managed student records</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Teachers</p><p className="mt-2 text-3xl font-bold text-ink-900">{loading ? "—" : teacherTotal}</p><p className="mt-1 text-xs text-slate-500">Faculty and role records</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Open cases</p><p className="mt-2 text-3xl font-bold text-brand-700">{loading ? "—" : caseSummary?.open_cases ?? 0}</p><p className="mt-1 text-xs text-slate-500">Students needing support action</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Completed cases</p><p className="mt-2 text-3xl font-bold text-emerald-700">{loading ? "—" : caseSummary?.completed_cases ?? 0}</p><p className="mt-1 text-xs text-slate-500">Persisted case completions</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Resolution rate</p><p className="mt-2 text-3xl font-bold text-brand-700">{loading ? "—" : `${caseSummary?.resolution_rate ?? 0}%`}</p><p className="mt-1 text-xs text-slate-500">Completed cases versus current open cases</p></Card><Card className="p-4"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-400">Departments</p><p className="mt-2 text-3xl font-bold text-ink-900">{loading ? "—" : new Set(students.map((student) => student.department)).size}</p><p className="mt-1 text-xs text-slate-500">Mapped academic units</p></Card></section>
      <Card as="section"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Academic configuration</p><h2 className="mt-1 text-lg font-bold text-ink-900">Risk thresholds</h2></div><p className="max-w-md text-xs text-slate-500">These settings are stored for future model runs and risk calculations.</p></div><form onSubmit={(event) => void saveConfig(event)} className="u8-filter-grid mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-[220px_220px_auto] lg:items-end"><label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">GPA threshold<input type="number" min="0" max="10" step="0.1" value={config.gpa_threshold} onChange={(event) => setConfig({ ...config, gpa_threshold: Number(event.target.value) })} className="min-w-0 rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-ink-900" /></label><label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">Attendance threshold (%)<input type="number" min="0" max="100" step="0.5" value={config.attendance_threshold} onChange={(event) => setConfig({ ...config, attendance_threshold: Number(event.target.value) })} className="min-w-0 rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal text-ink-900" /></label><button type="submit" disabled={saving} className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">{saving ? "Saving..." : saved ? "Saved" : "Save thresholds"}</button></form></Card>
      <Card as="section" className="min-w-0 p-0"><div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 xl:flex-row xl:items-end xl:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Reference records</p><h2 className="mt-1 text-lg font-bold text-ink-900">Students and teachers</h2></div><div className="grid min-w-0 gap-2 sm:grid-cols-[auto_minmax(0,300px)]"><div className="flex rounded-lg border border-slate-200 bg-slate-50 p-1"><button type="button" onClick={() => setTab("students")} aria-pressed={tab === "students"} className={`rounded-md px-3 py-1.5 text-xs font-semibold ${tab === "students" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"}`}>Students</button><button type="button" onClick={() => setTab("teachers")} aria-pressed={tab === "teachers"} className={`rounded-md px-3 py-1.5 text-xs font-semibold ${tab === "teachers" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"}`}>Teachers</button><button type="button" onClick={() => setTab("audit")} aria-pressed={tab === "audit"} className={`rounded-md px-3 py-1.5 text-xs font-semibold ${tab === "audit" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"}`}>Audit log</button></div><label className="sr-only" htmlFor="admin-record-search">Search records</label><input id="admin-record-search" aria-label="Search records" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, ID, department or role" className="min-w-0 rounded-lg border border-slate-200 px-3 py-2 text-sm" /></div></div><div className="p-3 md:p-5">{loading ? <p className="px-2 py-8 text-sm text-slate-500">Loading records...</p> : tab === "students" ? <><Table columns={studentColumns} rows={pagedStudents} rowKey={(row) => row.student_id} caption="Admin student records" emptyMessage="No matching students." /><Pagination page={safePage} totalPages={totalPages} totalRows={studentTotal} onPageChange={setPage} /></> : <><Table columns={teacherColumns} rows={pagedTeachers} rowKey={(row) => row.teacher_id} caption="Admin teacher records" emptyMessage="No matching teachers." /><Pagination page={safePage} totalPages={totalPages} totalRows={teacherTotal} onPageChange={setPage} /></>}</div></Card>
    </div>
  </InstitutionalShell>;
}
