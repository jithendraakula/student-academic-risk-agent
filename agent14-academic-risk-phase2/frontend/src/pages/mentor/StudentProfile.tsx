import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Card from "../../components/Card";
import RiskGauge from "../../components/RiskGauge";
import StatusDot from "../../components/StatusDot";
import { getRiskProfile, type RiskProfileResponse } from "../../features/mentor/api";
import { riskPercent, riskTone } from "../../features/mentor/formatters";
import { useAuth } from "../../context/AuthContext";

function RiskPanel({ title, result }: { title: string; result: { risk_probability: number; risk_level: string; confidence: string; top_factors: Array<{ feature: string; value: unknown }> } }) {
  return (
    <Card as="article" className="flex h-full flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-sm font-semibold text-ink-900">{title}</h2>
        <span className={`rounded-full border px-2 py-1 text-[11px] font-semibold uppercase tracking-wide ${riskTone(result.risk_level)}`}>
          {result.risk_level}
        </span>
      </div>
      <RiskGauge score={result.risk_probability * 100} label="Risk" size="sm" />
      <div className="border-t border-slate-100 pt-3">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Contributing factors</p>
        <ul className="space-y-2 text-sm text-ink-700">
          {result.top_factors.slice(0, 3).map((factor) => (
            <li key={factor.feature} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" aria-hidden="true" />
              <span>{factor.feature}{factor.value !== null && factor.value !== undefined ? ` (${String(factor.value)})` : ""}</span>
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-auto text-xs text-slate-500">Model confidence: <strong className="text-ink-700">{result.confidence}</strong> · {riskPercent(result.risk_probability)} probability</p>
    </Card>
  );
}

export default function StudentProfile() {
  const { studentId } = useParams<{ studentId: string }>();
  const { user } = useAuth();
  const backPath = user?.role === "hod" ? "/hod" : user?.role === "dean" ? "/dean" : "/mentor";
  const [profile, setProfile] = useState<RiskProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;
    getRiskProfile(studentId).then(setProfile).catch(() => setError("This student profile could not be loaded."));
  }, [studentId]);

  if (error) return <main className="min-h-screen p-6"><p className="text-sm text-red-700">{error}</p><Link className="mt-4 inline-block text-sm font-semibold text-brand-600" to={backPath}>Back to workspace</Link></main>;
  if (!profile) return <main className="min-h-screen p-6"><p className="text-sm text-slate-500">Loading student profile...</p></main>;

  const overall = Math.max(...profile.risks.course_failure.map((risk) => risk.risk_probability), profile.risks.backlog.risk_probability, profile.risks.gpa_threshold.risk_probability, profile.risks.attendance_shortage.risk_probability, profile.risks.discontinuation.risk_probability);

  return (
    <main className="min-h-screen bg-canvas">
      <header className="border-b border-slate-200 bg-white px-5 py-4 md:px-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <Link to={backPath} className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-600">{user?.role === "hod" ? "HOD workspace" : user?.role === "dean" ? "Dean workspace" : "Mentor workspace"}</Link>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-ink-900">{profile.student.student_name}</h1>
            <p className="mt-1 text-sm text-slate-500">{profile.student.student_id} · {profile.student.department} · Batch {profile.student.batch} · Section {profile.student.section}</p>
          </div>
          <StatusDot status={overall >= 0.75 ? "alert" : overall >= 0.5 ? "active" : "idle"} label={`${Math.round(overall * 100)}% highest risk`} />
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-6 px-5 py-6 md:px-8">
        <section>
          <div className="mb-3 flex items-end justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Risk profile</p><h2 className="text-lg font-bold text-ink-900">Five signals, one support plan</h2></div>
            <span className="text-xs text-slate-500">Use this view to plan the next mentor action.</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <RiskPanel title="Backlog accumulation" result={profile.risks.backlog} />
            <RiskPanel title="GPA threshold" result={profile.risks.gpa_threshold} />
            <RiskPanel title="Attendance shortage" result={profile.risks.attendance_shortage} />
            <RiskPanel title="Support attention" result={profile.risks.discontinuation} />
          </div>
        </section>

        <Card className="border-brand-100 bg-brand-50/40">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-600">Active configuration</p>
              <p className="mt-1 text-sm text-ink-700">GPA threshold: <strong>{profile.thresholds.gpa_threshold.toFixed(1)}</strong> · Attendance threshold: <strong>{profile.thresholds.attendance_threshold}%</strong></p>
            </div>
            <p className="text-xs text-slate-500">Applied from Admin configuration</p>
          </div>
        </Card>

        <section>
          <div className="mb-3"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Course watch</p><h2 className="text-lg font-bold text-ink-900">Course failure risk</h2></div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {profile.risks.course_failure.map((course) => (
              <Card key={course.course_id} className="p-4">
                <p className="truncate text-sm font-semibold text-ink-900" title={course.course_name}>{course.course_name}</p>
                <p className="mt-1 text-xs text-slate-500">{course.course_id}</p>
                <div className="mt-4"><RiskGauge score={course.risk_probability * 100} label="Failure risk" size="sm" /></div>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
