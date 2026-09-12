import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Card from "../../components/Card";
import PageHeader from "../../components/PageHeader";
import { getRiskProfile, type RiskProfileResponse } from "../../features/mentor/api";
import { riskTone } from "../../features/mentor/formatters";
import { useAuth } from "../../context/AuthContext";


function RiskPanel({ title, result }: { title: string; result: { risk_probability: number; risk_level: string; confidence: string; top_factors: Array<{ feature: string; value: unknown }> } }) {
  const borderColor = result.risk_level === "CRITICAL" ? "border-red-300 bg-red-50" :
                      result.risk_level === "HIGH" ? "border-orange-300 bg-orange-50" :
                      result.risk_level === "MEDIUM" ? "border-yellow-300 bg-yellow-50" :
                      "border-green-300 bg-green-50";

  return (
    <Card as="article" className={`flex h-full flex-col gap-3 ${borderColor}`}>
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex-1">
          <p className="text-2xl font-bold text-ink-900">{Math.round(result.risk_probability * 100)}%</p>
          <span className={`mt-1 inline-block rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${riskTone(result.risk_level)}`}>
            {result.risk_level}
          </span>
        </div>
      </div>
      
      <div className="border-t border-slate-200 pt-3">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Top Factors:</p>
        <ul className="space-y-1 text-xs text-ink-700">
          {result.top_factors.slice(0, 2).map((factor) => (
            <li key={factor.feature} className="flex gap-2">
              <span className="shrink-0">•</span>
              <span>{factor.feature}{factor.value !== null && factor.value !== undefined ? ` (${String(factor.value)})` : ""}</span>
            </li>
          ))}
        </ul>
      </div>

      <button className="mt-auto inline-flex text-xs font-semibold text-brand-600 hover:text-brand-700">
        View Details →
      </button>
    </Card>
  );
}

export default function StudentProfile() {
  const { studentId } = useParams<{ studentId: string }>();
  const { user } = useAuth();
  const backPath = user?.role === "hod" ? "/hod" : user?.role === "dean" ? "/dean" : "/mentor";
  const [profile, setProfile] = useState<RiskProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getRiskStatus = (score: number) => {
    if (score >= 0.75) return { label: "CRITICAL", emoji: "🔴", color: "text-red-700 border-red-300 bg-red-50" };
    if (score >= 0.5) return { label: "HIGH", emoji: "🟠", color: "text-orange-700 border-orange-300 bg-orange-50" };
    if (score >= 0.25) return { label: "MEDIUM", emoji: "🟡", color: "text-yellow-700 border-yellow-300 bg-yellow-50" };
    return { label: "LOW", emoji: "🟢", color: "text-green-700 border-green-300 bg-green-50" };
  };

  const getMetricColor = (value: number, threshold: number, isLowerBetter: boolean = false) => {
    const isSafe = isLowerBetter ? value <= threshold : value >= threshold;
    return isSafe ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50";
  };

  useEffect(() => {
    if (!studentId) return;
    getRiskProfile(studentId).then(setProfile).catch(() => setError("This student profile could not be loaded."));
  }, [studentId]);

  if (error) return <main className="min-h-screen p-6"><p className="text-sm text-red-700">{error}</p><Link className="mt-4 inline-block text-sm font-semibold text-brand-600" to={backPath}>Back to workspace</Link></main>;
  if (!profile) return <main className="min-h-screen p-6"><p className="text-sm text-slate-500">Loading student profile...</p></main>;

  const overall = Math.max(...profile.risks.course_failure.map((risk) => risk.risk_probability), profile.risks.backlog.risk_probability, profile.risks.gpa_threshold.risk_probability, profile.risks.attendance_shortage.risk_probability, profile.risks.discontinuation.risk_probability);

  return (
    <main className="min-h-screen bg-canvas">
      <PageHeader 
        title={profile.student.student_name} 
        subtitle={`${profile.student.student_id} · ${profile.student.department} · Batch ${profile.student.batch} · Section ${profile.student.section}`}
        badge={
          <div className={`rounded-lg border px-4 py-3 text-center ${getRiskStatus(overall).color}`}>
            <p className="text-2xl">{getRiskStatus(overall).emoji}</p>
            <p className="mt-1 text-xs font-semibold uppercase">{getRiskStatus(overall).label}</p>
            <p className="mt-0.5 text-sm font-bold">{Math.round(overall * 100)}% Risk</p>
          </div>
        }
      />

      <div className="mx-auto max-w-7xl space-y-6 px-5 py-6 md:px-8">
        <div>
          <Link to={backPath} className="text-sm font-semibold text-brand-600">← Back to {user?.role === "hod" ? "HOD workspace" : user?.role === "dean" ? "Dean workspace" : "Mentor workspace"}</Link>
        </div>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className={`flex flex-col border ${getMetricColor(profile.student_metrics.current_gpa, profile.thresholds.gpa_threshold)}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">🎓</p>
              <p className="text-lg">{profile.student_metrics.current_gpa < profile.thresholds.gpa_threshold ? "🔴" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Current GPA</p>
            <p className="mt-1 text-3xl font-bold">{profile.student_metrics.current_gpa}</p>
          </Card>

          <Card className={`flex flex-col border ${getMetricColor(profile.student_metrics.attendance, profile.thresholds.attendance_threshold)}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">📚</p>
              <p className="text-lg">{profile.student_metrics.attendance < profile.thresholds.attendance_threshold ? "🔴" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Attendance</p>
            <p className="mt-1 text-3xl font-bold">{profile.student_metrics.attendance}%</p>
          </Card>

          <Card className={`flex flex-col border ${profile.student_metrics.backlogs > 0 ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">📖</p>
              <p className="text-lg">{profile.student_metrics.backlogs > 2 ? "🔴" : profile.student_metrics.backlogs > 0 ? "🟠" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Backlogs</p>
            <p className="mt-1 text-3xl font-bold">{profile.student_metrics.backlogs}</p>
          </Card>

          <Card className="flex flex-col border border-slate-200 bg-white">
            <div className="flex items-start justify-between">
              <p className="text-2xl">📊</p>
              <p className="text-lg">🟢</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Current CGPA</p>
            <p className="mt-1 text-3xl font-bold">{profile.student_metrics.current_cgpa}</p>
          </Card>

          <Card className="flex flex-col border border-slate-200 bg-white">
            <div className="flex items-start justify-between">
              <p className="text-2xl">✏️</p>
              <p className="text-lg">🟢</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Internal Marks</p>
            <p className="mt-1 text-3xl font-bold">{profile.student_metrics.internal_marks}</p>
          </Card>

          <Card className={`flex flex-col border ${profile.student_metrics.absence_rate > (100 - profile.thresholds.attendance_threshold) ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">❌</p>
              <p className="text-lg">{profile.student_metrics.absence_rate > (100 - profile.thresholds.attendance_threshold) ? "🔴" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Absence Rate</p>
            <p className="mt-1 text-3xl font-bold">{profile.student_metrics.absence_rate}%</p>
          </Card>
        </section>

        <section>
          <div className="mb-3 flex items-end justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Risk Overview</p><h2 className="text-lg font-bold text-ink-900">Five risk signals analyzed</h2></div>
            <span className="text-xs text-slate-500">Model-based assessment with confidence scores</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <RiskPanel title="Backlog accumulation" result={profile.risks.backlog} />
            <RiskPanel title="GPA threshold" result={profile.risks.gpa_threshold} />
            <RiskPanel title="Attendance shortage" result={profile.risks.attendance_shortage} />
            <RiskPanel title="Support attention" result={profile.risks.discontinuation} />
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <Card>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
              Overall Risk Status
            </p>

            <div className={`mt-4 rounded-lg border p-4 text-center ${getRiskStatus(overall).color}`}>
              <p className="text-4xl">{getRiskStatus(overall).emoji}</p>
              <p className="mt-2 text-sm font-semibold uppercase">{getRiskStatus(overall).label}</p>
              <p className="mt-1 text-2xl font-bold">{Math.round(overall * 100)}%</p>
            </div>

            <div className="mt-4 border-t border-slate-200 pt-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-600 mb-3">Risk Drivers:</p>
              <ul className="space-y-2 text-sm text-ink-700">
                <li className="flex items-center justify-between">
                  <span>Attendance</span>
                  {profile.risks.attendance_shortage.risk_probability > 0.5 && <span className="text-lg">🔴</span>}
                  {profile.risks.attendance_shortage.risk_probability <= 0.5 && profile.risks.attendance_shortage.risk_probability > 0.25 && <span className="text-lg">🟠</span>}
                  {profile.risks.attendance_shortage.risk_probability <= 0.25 && <span className="text-lg">🟢</span>}
                </li>
                <li className="flex items-center justify-between">
                  <span>GPA</span>
                  {profile.risks.gpa_threshold.risk_probability > 0.5 && <span className="text-lg">🔴</span>}
                  {profile.risks.gpa_threshold.risk_probability <= 0.5 && profile.risks.gpa_threshold.risk_probability > 0.25 && <span className="text-lg">🟠</span>}
                  {profile.risks.gpa_threshold.risk_probability <= 0.25 && <span className="text-lg">🟢</span>}
                </li>
                <li className="flex items-center justify-between">
                  <span>Backlogs</span>
                  {profile.risks.backlog.risk_probability > 0.5 && <span className="text-lg">🔴</span>}
                  {profile.risks.backlog.risk_probability <= 0.5 && profile.risks.backlog.risk_probability > 0.25 && <span className="text-lg">🟠</span>}
                  {profile.risks.backlog.risk_probability <= 0.25 && <span className="text-lg">🟢</span>}
                </li>
              </ul>
            </div>
          </Card>

          <Card>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
              Intervention Plan
            </p>

            <ul className="mt-4 space-y-3 text-sm">
              {profile.risks.discontinuation.risk_probability > 0.5 && (
                <li className="flex gap-3">
                  <span>🔴</span>
                  <span className="font-medium">Parent Meeting Required</span>
                </li>
              )}

              {profile.risks.attendance_shortage.risk_probability > 0.5 && (
                <li className="flex gap-3">
                  <span>🔴</span>
                  <span className="font-medium">Attendance Counselling Required</span>
                </li>
              )}

              {profile.risks.gpa_threshold.risk_probability > 0.5 && (
                <li className="flex gap-3">
                  <span>🟠</span>
                  <span className="font-medium">Academic Recovery Plan Required</span>
                </li>
              )}

              {profile.risks.backlog.risk_probability > 0.5 && (
                <li className="flex gap-3">
                  <span>🟠</span>
                  <span className="font-medium">Backlog Recovery Mentoring Required</span>
                </li>
              )}

              {overall >= 0.5 && (
                <li className="flex gap-3">
                  <span>🔴</span>
                  <span className="font-medium">Escalate to HOD</span>
                </li>
              )}

              {overall < 0.5 && (
                <li className="flex gap-3">
                  <span>✅</span>
                  <span className="font-medium">Continue regular monitoring</span>
                </li>
              )}
            </ul>
          </Card>
        </section>

        <Card className="border-slate-300 bg-slate-50">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">
            Recent Risk Events Timeline
          </p>

          <ul className="mt-4 space-y-4 text-sm">
            <li className="flex gap-4 border-l-2 border-red-300 pl-4">
              <div className="mt-0.5">📅</div>
              <div>
                <p className="font-bold text-ink-900">Sep 20</p>
                <p className="text-slate-600">Escalated to HOD for intervention</p>
              </div>
            </li>
            {profile.student_metrics.attendance < profile.thresholds.attendance_threshold && (
              <li className="flex gap-4 border-l-2 border-orange-300 pl-4">
                <div className="mt-0.5">📅</div>
                <div>
                  <p className="font-bold text-ink-900">Sep 15</p>
                  <p className="text-slate-600">Attendance dropped below {profile.thresholds.attendance_threshold}%</p>
                </div>
              </li>
            )}
            {profile.student_metrics.backlogs > 0 && (
              <li className="flex gap-4 border-l-2 border-orange-300 pl-4">
                <div className="mt-0.5">📅</div>
                <div>
                  <p className="font-bold text-ink-900">Sep 08</p>
                  <p className="text-slate-600">Backlog count increased to {profile.student_metrics.backlogs}</p>
                </div>
              </li>
            )}
            {profile.student_metrics.current_gpa < profile.thresholds.gpa_threshold && (
              <li className="flex gap-4 border-l-2 border-red-300 pl-4">
                <div className="mt-0.5">📅</div>
                <div>
                  <p className="font-bold text-ink-900">Sep 02</p>
                  <p className="text-slate-600">GPA dropped below {profile.thresholds.gpa_threshold}</p>
                </div>
              </li>
            )}
          </ul>
        </Card>

        <section>
          <div className="mb-3"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Course Risk</p><h2 className="text-lg font-bold text-ink-900">Course failure risk by subject</h2></div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {profile.risks.course_failure.map((course) => (
              <Card key={course.course_id} className="flex flex-col items-center justify-center text-center p-4">
                <p className="truncate text-xs font-semibold text-slate-500" title={course.course_name}>{course.course_id}</p>
                <p className="mt-3 text-3xl font-bold text-ink-900">{Math.round(course.risk_probability * 100)}%</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  {course.risk_probability >= 0.75 ? "Critical" : course.risk_probability >= 0.5 ? "High" : course.risk_probability >= 0.25 ? "Medium" : "Low"}
                </p>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
