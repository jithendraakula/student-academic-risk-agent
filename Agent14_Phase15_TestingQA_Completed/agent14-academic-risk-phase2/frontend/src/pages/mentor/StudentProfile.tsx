import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import { getRiskProfile, runWhatIf, type RiskProfileResponse, type WhatIfResponse } from "../../features/mentor/api";
import { runMentorCopilot, type CopilotIntent, type CopilotResponse } from "../../features/mentor/ai";
import { riskTone } from "../../features/mentor/formatters";
import { useAuth } from "../../context/AuthContext";


function RiskPanel({ title, result }: { title: string; result: { risk_probability: number; risk_level: string; confidence: string; top_factors: Array<{ feature: string; value: unknown }> } }) {
  const borderColor = result.risk_level === "CRITICAL" ? "border-red-300 bg-red-50" :
                      result.risk_level === "HIGH" ? "border-orange-300 bg-orange-50" :
                      result.risk_level === "MEDIUM" ? "border-yellow-300 bg-yellow-50" :
                      "border-green-300 bg-green-50";

  return (
    <Card as="article" className={`flex h-full flex-col gap-3 transition-shadow duration-150 hover:shadow-md ${borderColor}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">{title}</p>
          <p className="mt-1 text-2xl font-extrabold text-ink-900">{Math.round(result.risk_probability * 100)}%</p>
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
  const [whatIf, setWhatIf] = useState<WhatIfResponse | null>(null);
  const [lastWhatIfPayload, setLastWhatIfPayload] = useState<Parameters<typeof runWhatIf>[1] | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [whatIfAttendance, setWhatIfAttendance] = useState("");
  const [whatIfGpa, setWhatIfGpa] = useState("");
  const [whatIfBacklogs, setWhatIfBacklogs] = useState("");
  const [whatIfAssignmentRate, setWhatIfAssignmentRate] = useState("");
  const [selectedCourse, setSelectedCourse] = useState("");
  const [courseAttendance, setCourseAttendance] = useState("");
  const [courseMarks, setCourseMarks] = useState("");
  const [copilot, setCopilot] = useState<CopilotResponse | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotError, setCopilotError] = useState<string | null>(null);

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

  async function handleWhatIf(event: React.FormEvent) {
    event.preventDefault();
    if (!studentId) return;
    const payload: Parameters<typeof runWhatIf>[1] = {};
    if (whatIfAttendance !== "") payload.attendance_percentage = Number(whatIfAttendance);
    if (whatIfGpa !== "") payload.gpa = Number(whatIfGpa);
    if (whatIfBacklogs !== "") payload.backlog_count = Number(whatIfBacklogs);
    if (whatIfAssignmentRate !== "") payload.assignment_completion_rate = Number(whatIfAssignmentRate) / 100;
    if (selectedCourse && (courseAttendance !== "" || courseMarks !== "")) {
      payload.course = { course_id: selectedCourse };
      if (courseAttendance !== "") payload.course.course_attendance_percentage = Number(courseAttendance);
      if (courseMarks !== "") {
        const mark = Number(courseMarks);
        payload.course.internal_marks = mark;
        payload.course.midterm_marks = mark;
        payload.course.quiz_average = mark;
        payload.course.assignment_average = mark;
        payload.course.practical_marks = mark;
      }
    }
    if (!Object.keys(payload).length) {
      setError("Set at least one what-if value.");
      return;
    }
    setSimulating(true);
    try {
      const simulation = await runWhatIf(studentId, payload);
      setWhatIf(simulation);
      setLastWhatIfPayload(payload);
      setError(null);
    } catch {
      setError("The what-if scenario could not be calculated.");
    } finally {
      setSimulating(false);
    }
  }

  async function handleCopilot(intent: CopilotIntent) {
    if (!studentId) return;
    setCopilotLoading(true);
    setCopilotError(null);
    try {
      const result = await runMentorCopilot(studentId, intent, intent === "what_if_explanation" && lastWhatIfPayload ? { what_if: lastWhatIfPayload } : undefined);
      setCopilot(result);
    } catch (requestError: any) {
      setCopilotError(requestError?.response?.data?.detail || "Mentor AI is unavailable. Configure the backend AI provider and API key.");
    } finally {
      setCopilotLoading(false);
    }
  }

  // Guard order matters: only treat this as a fatal, full-page error when the
  // profile itself never loaded. Once a profile is loaded, later errors (e.g.
  // a failed what-if simulation) should surface inline instead of tearing
  // down the whole page.
  if (!profile) {
    if (error) return <main className="min-h-screen p-6"><p className="text-sm text-red-700">{error}</p><Link className="mt-4 inline-block text-sm font-semibold text-brand-600" to={backPath}>Back to workspace</Link></main>;
    return <main className="min-h-screen p-6"><p className="text-sm text-slate-500">Loading student profile...</p></main>;
  }

  // Guard against an empty course_failure array: reduce with a safe 0
  // fallback instead of spreading a possibly-empty (or very large) array
  // into Math.max, which would otherwise risk -Infinity or a stack overflow.
  const courseFailureMax = profile.risks.course_failure.reduce((max, risk) => Math.max(max, risk.risk_probability), 0);
  const overall = Math.max(courseFailureMax, profile.risks.backlog.risk_probability, profile.risks.gpa_threshold.risk_probability, profile.risks.attendance_shortage.risk_probability, profile.risks.discontinuation.risk_probability);

  return (
    <InstitutionalShell
      eyebrow="CSE · VIGNAN'S UNIVERSITY"
      title="STUDENT ACADEMIC RISK MANAGEMENT"
      subtitle={`${profile.student.student_id} · ${profile.student.department} · Batch ${profile.student.batch} · Section ${profile.student.section}`}
    >
      <div className="space-y-6">
        <Link to={backPath} className="inline-flex items-center gap-2 text-xs font-bold text-brand-700 hover:text-brand-800">← Back to {user?.role === "hod" ? "HOD workspace" : user?.role === "dean" ? "Dean workspace" : "Mentor workspace"}</Link>

        <section className="animate-fade-in flex flex-col gap-4 rounded-2xl border border-[#cfe0f8] bg-gradient-to-r from-white via-[#f7fbff] to-[#eaf3ff] p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-brand-600">Authorized student profile</p>
            <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-[#18345f]">{profile.student.student_name}</h2>
            <p className="mt-1 text-sm text-slate-500">Mentor-led review · current academic cycle</p>
          </div>
          <div className={`flex items-center gap-3 rounded-2xl border px-4 py-3 ${getRiskStatus(overall).color}`}>
            <span className="text-2xl">{getRiskStatus(overall).emoji}</span>
            <div><p className="text-[10px] font-bold uppercase tracking-[0.14em]">Overall risk</p><p className="text-lg font-extrabold">{Math.round(overall * 100)}% · {getRiskStatus(overall).label}</p></div>
          </div>
        </section>

        {error ? <div role="alert" className="animate-fade-in rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

        <Card as="section" className="border-brand-200 bg-brand-50/30">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-600">What-If Simulator</p>
              <h2 className="mt-1 text-lg font-bold text-ink-900">Test academic improvement scenarios</h2>
              <p className="mt-1 text-sm text-slate-500">Explore estimated risk changes without changing the student's actual record.</p>
            </div>
            <span className="rounded-full border border-brand-200 bg-white px-3 py-1 text-xs font-semibold text-brand-700">Non-persistent</span>
          </div>
          <form onSubmit={(event) => void handleWhatIf(event)} className="mt-4 grid gap-3 md:grid-cols-4">
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Attendance %<input type="number" min="0" max="100" step="0.1" value={whatIfAttendance} onChange={(e) => setWhatIfAttendance(e.target.value)} placeholder={String(profile.student_metrics.attendance)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal" /></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">GPA<input type="number" min="0" max="10" step="0.01" value={whatIfGpa} onChange={(e) => setWhatIfGpa(e.target.value)} placeholder={String(profile.student_metrics.current_gpa)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal" /></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Backlog count<input type="number" min="0" max="30" value={whatIfBacklogs} onChange={(e) => setWhatIfBacklogs(e.target.value)} placeholder={String(profile.student_metrics.backlogs)} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal" /></label>
            <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Assignment completion %<input type="number" min="0" max="100" step="1" value={whatIfAssignmentRate} onChange={(e) => setWhatIfAssignmentRate(e.target.value)} placeholder="e.g. 90" className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-normal" /></label>
            <div className="md:col-span-4 grid gap-3 rounded-lg border border-slate-200 bg-white p-3 md:grid-cols-3">
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Course<select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal"><option value="">No course scenario</option>{profile.risks.course_failure.map((course) => <option key={course.course_id} value={course.course_id}>{course.course_id} · {course.course_name}</option>)}</select></label>
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Course attendance %<input type="number" min="0" max="100" step="0.1" value={courseAttendance} onChange={(e) => setCourseAttendance(e.target.value)} disabled={!selectedCourse} placeholder="e.g. 90" className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal disabled:bg-slate-50" /></label>
              <label className="flex flex-col gap-1 text-xs font-semibold text-slate-600">Course marks (all assessment fields)<input type="number" min="0" max="100" step="0.1" value={courseMarks} onChange={(e) => setCourseMarks(e.target.value)} disabled={!selectedCourse} placeholder="e.g. 80" className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-normal disabled:bg-slate-50" /></label>
            </div>
            <button type="submit" disabled={simulating} className="md:col-span-4 justify-self-start rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">{simulating ? "Calculating..." : "Simulate scenario"}</button>
          </form>
          {whatIf ? (
            <div className="animate-fade-in mt-4 grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-400">Priority change</p><p className={`mt-1 text-2xl font-bold ${whatIf.interpretation.improved ? "text-green-700" : "text-orange-700"}`}>{whatIf.interpretation.overall_priority_delta > 0 ? "+" : ""}{whatIf.interpretation.overall_priority_delta}</p><p className="text-xs text-slate-500">Lower is better</p></div>
              <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-400">Baseline</p><p className="mt-1 text-xl font-bold">{whatIf.baseline.summary.priority_score}</p><p className="text-xs text-slate-500">Priority · {whatIf.baseline.summary.risk_level}</p></div>
              <div className="rounded-lg border border-slate-200 bg-white p-4"><p className="text-xs font-semibold uppercase text-slate-400">Simulated</p><p className="mt-1 text-xl font-bold">{whatIf.simulated.summary.priority_score}</p><p className="text-xs text-slate-500">Priority · {whatIf.simulated.summary.risk_level}</p></div>
              <div className="md:col-span-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">{whatIf.interpretation.warning}</div>
            </div>
          ) : null}
        </Card>

        {user?.role === "mentor" && (
          <Card as="section" className="border-slate-300 bg-white">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Mentor AI Copilot</p>
                <h2 className="mt-1 text-lg font-bold text-ink-900">Turn risk evidence into a mentor action plan</h2>
                <p className="mt-1 max-w-2xl text-sm text-slate-500">AI explains the canonical ML evidence and suggests supportive next steps. It does not calculate or change risk scores.</p>
              </div>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">Grounded in RiskPrediction</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" onClick={() => void handleCopilot("risk_summary")} disabled={copilotLoading} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60">{copilotLoading ? "Thinking..." : "Explain current risk"}</button>
              <button type="button" onClick={() => void handleCopilot("intervention_plan")} disabled={copilotLoading} className="rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">Recommend intervention</button>
              {lastWhatIfPayload && <button type="button" onClick={() => void handleCopilot("what_if_explanation")} disabled={copilotLoading} className="rounded-lg border border-brand-300 px-3 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50 disabled:opacity-60">Explain last what-if</button>}
            </div>
            {copilotError && <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{copilotError}</p>}
            {copilot && (
              <div className="animate-fade-in mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-slate-200 p-4 md:col-span-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">{copilot.intent.replaceAll("_", " ")}</p>
                    <span className="text-xs text-slate-400">{copilot.provider} · {copilot.model} · {copilot.grounded ? "grounded" : "ungrounded"}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-ink-700">{copilot.explanation}</p>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Recommended actions</p>
                  <ul className="mt-2 space-y-2 text-sm text-ink-700">{copilot.recommended_actions.map((action) => <li key={action} className="flex gap-2"><span>•</span><span>{action}</span></li>)}</ul>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Priority rationale</p>
                  <p className="mt-2 text-sm leading-6 text-ink-700">{copilot.priority_rationale}</p>
                  {copilot.cautions.length > 0 && <div className="mt-3 border-t border-slate-200 pt-3"><p className="text-xs font-semibold uppercase text-slate-500">Cautions</p><ul className="mt-1 space-y-1 text-xs text-slate-600">{copilot.cautions.map((item) => <li key={item}>• {item}</li>)}</ul></div>}
                </div>
              </div>
            )}
          </Card>
        )}

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className={`flex flex-col border ${getMetricColor(profile.student_metrics.current_gpa, profile.thresholds.gpa_threshold)}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">🎓</p>
              <p className="text-lg">{profile.student_metrics.current_gpa < profile.thresholds.gpa_threshold ? "🔴" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Current GPA</p>
            <p className="mt-1 text-2xl font-bold">{profile.student_metrics.current_gpa}</p>
          </Card>

          <Card className={`flex flex-col border ${getMetricColor(profile.student_metrics.attendance, profile.thresholds.attendance_threshold)}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">📚</p>
              <p className="text-lg">{profile.student_metrics.attendance < profile.thresholds.attendance_threshold ? "🔴" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Attendance</p>
            <p className="mt-1 text-2xl font-bold">{profile.student_metrics.attendance}%</p>
          </Card>

          <Card className={`flex flex-col border ${profile.student_metrics.backlogs > 0 ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">📖</p>
              <p className="text-lg">{profile.student_metrics.backlogs > 2 ? "🔴" : profile.student_metrics.backlogs > 0 ? "🟠" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Backlogs</p>
            <p className="mt-1 text-2xl font-bold">{profile.student_metrics.backlogs}</p>
          </Card>

          <Card className="flex flex-col border border-slate-200 bg-white">
            <div className="flex items-start justify-between">
              <p className="text-2xl">📊</p>
              <p className="text-lg">🟢</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Current CGPA</p>
            <p className="mt-1 text-2xl font-bold">{profile.student_metrics.current_cgpa}</p>
          </Card>

          <Card className="flex flex-col border border-slate-200 bg-white">
            <div className="flex items-start justify-between">
              <p className="text-2xl">✏️</p>
              <p className="text-lg">🟢</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Internal Marks</p>
            <p className="mt-1 text-2xl font-bold">{profile.student_metrics.internal_marks}</p>
          </Card>

          <Card className={`flex flex-col border ${profile.student_metrics.absence_rate > (100 - profile.thresholds.attendance_threshold) ? "border-red-200 bg-red-50" : "border-green-200 bg-green-50"}`}>
            <div className="flex items-start justify-between">
              <p className="text-2xl">❌</p>
              <p className="text-lg">{profile.student_metrics.absence_rate > (100 - profile.thresholds.attendance_threshold) ? "🔴" : "🟢"}</p>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-[0.08em] text-slate-400">Absence Rate</p>
            <p className="mt-1 text-2xl font-bold">{profile.student_metrics.absence_rate}%</p>
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

        <section className="grid items-stretch gap-4 md:grid-cols-2">
          <Card>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
              Overall Risk Status
            </p>

            <div className={`mt-4 rounded-lg border p-4 text-center ${getRiskStatus(overall).color}`}>
              <p className="text-3xl">{getRiskStatus(overall).emoji}</p>
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
    </InstitutionalShell>
  );
}