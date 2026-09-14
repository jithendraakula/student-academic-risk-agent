import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import Card from "../../components/Card";
import InstitutionalShell from "../../components/InstitutionalShell";
import { ActionButton, Icon, KeyValue, SectionHeading, StatusChip } from "../../components/AcademicUI";
import { getRiskProfile, markStudentCaseComplete, runWhatIf, type RiskProfileResponse, type RiskResult, type WhatIfResponse } from "../../features/mentor/api";
import { runMentorCopilot, type CopilotIntent, type CopilotResponse } from "../../features/mentor/ai";
import { readableRiskType } from "../../features/mentor/formatters";
import { useAuth } from "../../context/AuthContext";
import { notifyCaseWorkUpdated, subscribeToLiveCaseWorkUpdates } from "../../features/caseWorkEvents";
import CompleteCaseDialog, { type CompletionPayload } from "../../components/CompleteCaseDialog";

const RISK_META: Record<string, { label: string; description: string }> = {
  backlog: { label: "Backlog accumulation", description: "Risk of carrying additional unresolved courses." },
  gpa_threshold: { label: "GPA threshold", description: "Risk of remaining below the configured academic threshold." },
  attendance_shortage: { label: "Attendance shortage", description: "Risk associated with insufficient attendance." },
  support_attention: { label: "Support attention", description: "Restricted support-oriented continuity signal." },
  discontinuation: { label: "Support attention", description: "Restricted support-oriented continuity signal." },
  course_failure: { label: "Course failure", description: "Course-specific risk of failing a current subject." },
};

function riskLabel(level: string) {
  const normalized = level?.toUpperCase();
  return normalized === "MEDIUM" ? "MODERATE" : normalized || "LOW";
}

function score100(value: number) {
  return `${Math.round(value)} / 100`;
}

function percentage(value: number) {
  return `${Math.round(value * 100)}%`;
}

function evidenceFor(key: string, result: RiskResult, profile: RiskProfileResponse) {
  const factor = result.top_factors?.[0];
  if (factor?.feature) {
    return `${factor.feature}${factor.value !== null && factor.value !== undefined ? ` · ${String(factor.value)}` : ""}`;
  }
  if (key === "backlog") return `${profile.student_metrics.backlogs} unresolved course${profile.student_metrics.backlogs === 1 ? "" : "s"}`;
  if (key === "gpa_threshold") return `GPA ${profile.student_metrics.current_gpa} vs threshold ${profile.thresholds.gpa_threshold}`;
  if (key === "attendance_shortage") return `Attendance ${profile.student_metrics.attendance}% vs threshold ${profile.thresholds.attendance_threshold}%`;
  if (key === "support_attention") return profile.academic_context.primary_context_intent ? `Context: ${profile.academic_context.primary_context_intent.replaceAll("_", " ")}` : "Support-oriented continuity signal";
  if (key === "discontinuation") return profile.academic_context.primary_context_intent ? `Context: ${profile.academic_context.primary_context_intent.replaceAll("_", " ")}` : "Support-oriented continuity signal";
  return "Course-specific evidence is shown in the course review below.";
}

function SectionNote({ children }: { children: ReactNode }) {
  return <div className="ui-data-note mt-3">{children}</div>;
}

function RiskEvidenceRow({ title, result, note, evidence, courseName }: { title: string; result: RiskResult; note: string; evidence: string; courseName?: string }) {
  return (
    <article className="ui-case-panel p-4 md:p-5">
      <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.6fr)_150px_160px_minmax(0,1fr)] xl:items-start">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-extrabold text-ink-900">{title}</h3>
            <StatusChip level={riskLabel(result.risk_level)}>{riskLabel(result.risk_level)}</StatusChip>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">{note}</p>
          {courseName ? <p className="mt-2 text-xs font-semibold text-brand-700">Highest-priority course: {courseName}</p> : null}
        </div>
        <div className="border-t border-slate-100 pt-3 xl:border-l xl:border-t-0 xl:pl-4 xl:pt-0">
          <p className="ui-key-label">Risk</p>
          <p className="mt-1 text-2xl font-extrabold text-ink-900">{percentage(result.risk_probability)}</p>
          <p className="mt-1 text-[11px] text-slate-500">Probability</p>
        </div>
        <div className="border-t border-slate-100 pt-3 xl:border-l xl:border-t-0 xl:pl-4 xl:pt-0">
          <p className="ui-key-label">Priority</p>
          <p className="mt-1 text-lg font-extrabold text-brand-700">{score100(result.priority_score ?? result.risk_score ?? result.risk_probability * 100)}</p>
          <p className="mt-1 text-[11px] text-slate-500">Confidence: {result.confidence}</p>
        </div>
        <div className="min-w-0 border-t border-slate-100 pt-3 xl:border-l xl:border-t-0 xl:pl-4 xl:pt-0">
          <p className="ui-key-label">Evidence</p>
          <p className="mt-1 break-words text-xs font-semibold leading-5 text-slate-700">{evidence}</p>
        </div>
      </div>
    </article>
  );
}

function SkeletonProfile() {
  return (
    <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC REVIEW" subtitle="Loading authorized case">
      <div className="space-y-6" aria-busy="true">
        <div className="h-12 animate-pulse rounded-xl bg-white" />
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]"><div className="h-48 animate-pulse rounded-2xl bg-white" /><div className="h-48 animate-pulse rounded-2xl bg-white" /></div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[1, 2, 3, 4].map((item) => <div key={item} className="h-28 animate-pulse rounded-xl bg-white" />)}</div>
        <div className="space-y-3">{[1, 2, 3, 4, 5].map((item) => <div key={item} className="h-28 animate-pulse rounded-xl bg-white" />)}</div>
      </div>
    </InstitutionalShell>
  );
}

export default function StudentProfile() {
  const { studentId } = useParams<{ studentId: string }>();
  const { user } = useAuth();
  const backPath = user?.role === "hod" ? "/hod" : user?.role === "dean" ? "/dean" : "/mentor";
  const backLabel = user?.role === "hod" ? "HOD workspace" : user?.role === "dean" ? "Dean workspace" : "Mentor workspace";

  const [profile, setProfile] = useState<RiskProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [whatIf, setWhatIf] = useState<WhatIfResponse | null>(null);
  const [lastWhatIfPayload, setLastWhatIfPayload] = useState<Parameters<typeof runWhatIf>[1] | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [whatIfMode, setWhatIfMode] = useState<"attendance" | "gpa" | "backlog" | "assignment" | "course">("attendance");
  const [whatIfValue, setWhatIfValue] = useState("");
  const [selectedCourse, setSelectedCourse] = useState("");
  const [courseFactor, setCourseFactor] = useState<"course_attendance_percentage" | "internal_marks" | "assignment_completion_rate">("course_attendance_percentage");
  const [courseValue, setCourseValue] = useState("");
  const [copilot, setCopilot] = useState<CopilotResponse | null>(null);
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotError, setCopilotError] = useState<string | null>(null);
  const [completingAlertId, setCompletingAlertId] = useState<string | null>(null);
  const [caseCompleted, setCaseCompleted] = useState(false);

  useEffect(() => {
    if (!studentId) return;
    let active = true;
    setLoading(true);
    setError(null);
    getRiskProfile(studentId)
      .then((result) => {
        if (!active) return;
        setProfile(result);
        setCaseCompleted(Boolean(result.case_management?.case_completed));
        setWhatIfValue(String(Math.min(90, Math.max(result.student_metrics.attendance + 10, result.thresholds.attendance_threshold))));
      })
      .catch(() => { if (active) setError("This student case could not be loaded. The record may be outside your authorized scope."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [studentId]);

  const [completionDialogOpen, setCompletionDialogOpen] = useState(false);

  async function handleMarkComplete(payload: CompletionPayload) {
    if (user?.role !== "mentor" || !studentId) return;
    setCompletingAlertId(studentId);
    setError(null);
    try {
      await markStudentCaseComplete(studentId, payload);
      setCaseCompleted(true);
      setCompletionDialogOpen(false);
      notifyCaseWorkUpdated();
      const refreshed = await getRiskProfile(studentId);
      setProfile(refreshed);
    } catch {
      setError("The student case could not be marked as complete. Please try again.");
    } finally {
      setCompletingAlertId(null);
    }
  }


  useEffect(() => {
    const stop = subscribeToLiveCaseWorkUpdates(() => {
      if (!studentId) return;
      void getRiskProfile(studentId)
        .then((result) => {
          setProfile(result);
          setCaseCompleted(Boolean(result.case_management?.case_completed));
        })
        .catch(() => undefined);
    });
    return stop;
  }, [studentId]);
  const courseRisks = profile?.risks.course_failure ?? [];
  const highestCourseRisk = useMemo(() => courseRisks.reduce((best, item) => !best || (item.priority_score ?? item.risk_score ?? item.risk_probability * 100) > (best.priority_score ?? best.risk_score ?? best.risk_probability * 100) ? item : best, null as (typeof courseRisks[number]) | null), [courseRisks]);

  const currentSignals = useMemo(() => {
    if (!profile) return [] as Array<{ key: string; result: RiskResult; courseName?: string }>;
    const items: Array<{ key: string; result: RiskResult; courseName?: string }> = [
      { key: "backlog", result: profile.risks.backlog },
      { key: "gpa_threshold", result: profile.risks.gpa_threshold },
      { key: "attendance_shortage", result: profile.risks.attendance_shortage },
    ];
    if (highestCourseRisk) items.push({ key: "course_failure", result: highestCourseRisk, courseName: highestCourseRisk.course_name });
    if (profile.risks.discontinuation) items.push({ key: "support_attention", result: profile.risks.discontinuation });
    return items;
  }, [profile, highestCourseRisk]);

  const primarySignal = useMemo(() => {
    if (!profile?.current_status.primary_risk) return null;
    const key = profile.current_status.primary_risk === "discontinuation" ? "support_attention" : profile.current_status.primary_risk;
    if (key === "course_failure") return highestCourseRisk ? { key, result: highestCourseRisk } : null;
    const candidate = profile.risks[key as keyof Omit<RiskProfileResponse["risks"], "course_failure">];
    return candidate && !Array.isArray(candidate) ? { key, result: candidate } : null;
  }, [profile, highestCourseRisk]);

  const selectedCourseRisk = courseRisks.find((course) => course.course_id === selectedCourse);
  const courseFactorMeta = {
    course_attendance_percentage: { label: "Course attendance", suffix: "%", min: 0, max: 100, step: 1, current: selectedCourseRisk?.course_metrics?.course_attendance_percentage ?? null },
    internal_marks: { label: "Internal marks", suffix: "", min: 0, max: 100, step: 1, current: selectedCourseRisk?.course_metrics?.internal_marks ?? null },
    assignment_completion_rate: { label: "Assignment completion", suffix: "%", min: 0, max: 100, step: 5, current: selectedCourseRisk?.course_metrics ? selectedCourseRisk.course_metrics.assignment_completion_rate * 100 : null },
  }[courseFactor];

  const modeConfig = {
    attendance: { label: "Attendance", current: profile?.student_metrics.attendance ?? 0, suffix: "%", min: 0, max: 100, step: 1 },
    gpa: { label: "GPA", current: profile?.student_metrics.current_gpa ?? 0, suffix: "", min: 0, max: 10, step: 0.1 },
    backlog: { label: "Backlogs", current: profile?.student_metrics.backlogs ?? 0, suffix: "", min: 0, max: 12, step: 1 },
    assignment: { label: "Assignments", current: profile?.student_metrics.assignment_completion ?? 0, suffix: "%", min: 0, max: 100, step: 5 },
    course: { label: "Course factor", current: courseFactorMeta.current, suffix: courseFactorMeta.suffix, min: courseFactorMeta.min, max: courseFactorMeta.max, step: courseFactorMeta.step },
  }[whatIfMode];

  function recommendedTargetFor(mode: typeof whatIfMode) {
    if (!profile) return "";
    if (mode === "attendance") return String(Math.min(90, Math.max(profile.student_metrics.attendance + 10, profile.thresholds.attendance_threshold)));
    if (mode === "gpa") return String(Math.min(10, profile.student_metrics.current_gpa + 0.5));
    if (mode === "backlog") return String(Math.max(0, profile.student_metrics.backlogs - 1));
    if (mode === "assignment") return String(Math.min(100, Math.max(profile.student_metrics.assignment_completion + 15, 90)));
    return "";
  }

  function selectWhatIfMode(mode: typeof whatIfMode) {
    setWhatIfMode(mode);
    setWhatIf(null);
    setCopilot(null);
    setCopilotError(null);
    if (mode === "course") {
      setWhatIfValue("");
      setCourseValue("");
      return;
    }
    setWhatIfValue(recommendedTargetFor(mode));
  }

  function setScenarioPreset() {
    if (!profile) return;
    if (whatIfMode === "course") {
      if (!selectedCourseRisk) return;
      const current = Number(courseFactorMeta.current ?? 0);
      const target = courseFactor === "course_attendance_percentage" ? Math.min(90, current + 10) : courseFactor === "internal_marks" ? Math.min(85, current + 10) : Math.min(100, Math.max(current + 15, 90));
      setCourseValue(String(Math.round(target * 10) / 10));
      return;
    }
    setWhatIfValue(recommendedTargetFor(whatIfMode));
  }

  async function handleWhatIf(event: React.FormEvent) {
    event.preventDefault();
    if (!studentId) return;
    const payload: Parameters<typeof runWhatIf>[1] = {};
    if (whatIfMode === "course") {
      if (!selectedCourse || courseValue === "") return;
      const numeric = Number(courseValue);
      if (!Number.isFinite(numeric)) return;
      payload.course = { course_id: selectedCourse };
      if (courseFactor === "course_attendance_percentage") payload.course.course_attendance_percentage = numeric;
      if (courseFactor === "internal_marks") payload.course.internal_marks = numeric;
      if (courseFactor === "assignment_completion_rate") payload.course.assignment_completion_rate = numeric / 100;
    } else {
      if (whatIfValue === "") return;
      const numeric = Number(whatIfValue);
      if (!Number.isFinite(numeric)) return;
      if (whatIfMode === "attendance") payload.attendance_percentage = numeric;
      if (whatIfMode === "gpa") payload.gpa = numeric;
      if (whatIfMode === "backlog") payload.backlog_count = numeric;
      if (whatIfMode === "assignment") payload.assignment_completion_rate = numeric / 100;
    }
    setSimulating(true);
    try {
      const simulation = await runWhatIf(studentId, payload);
      setWhatIf(simulation);
      setLastWhatIfPayload(payload);
      setCopilot(null);
      setCopilotError(null);
      setError(null);
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || "The What-If scenario could not be calculated. Review the inputs and try again.");
    } finally { setSimulating(false); }
  }

  async function handleCopilot(intent: CopilotIntent) {
    if (!studentId) return;
    setCopilotLoading(true);
    setCopilotError(null);
    try {
      const result = await runMentorCopilot(studentId, intent, intent === "what_if_explanation" && lastWhatIfPayload ? { what_if: lastWhatIfPayload } : undefined);
      setCopilot(result);
    } catch (requestError: any) {
      setCopilotError(requestError?.response?.data?.detail || "Mentor AI is unavailable. Configure the backend AI provider when you are ready.");
    } finally { setCopilotLoading(false); }
  }

  if (loading) return <SkeletonProfile />;
  if (error || !profile) {
    return <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC REVIEW" subtitle="Authorized faculty workspace"><div className="rounded-xl border border-red-200 bg-red-50 p-5"><p className="text-sm font-semibold text-red-800">{error ?? "Student record unavailable."}</p><Link className="mt-4 inline-flex items-center gap-1 text-sm font-bold text-brand-700" to={backPath}><Icon name="back" />Return to {backLabel}</Link></div></InstitutionalShell>;
  }

  const statusLabel = riskLabel(profile.current_status.risk_level);
  const statusTone = statusLabel === "CRITICAL" ? "border-red-200 bg-red-50" : statusLabel === "HIGH" ? "border-orange-200 bg-orange-50" : statusLabel === "MODERATE" ? "border-amber-200 bg-amber-50" : "border-emerald-200 bg-emerald-50";
  const contextItems = profile.academic_context.observations.slice(0, 3);
  const primaryAction = profile.academic_context.primary_action_path?.recommended_action;

  return (
    <InstitutionalShell eyebrow="CSE · VIGNAN'S UNIVERSITY" title="STUDENT ACADEMIC REVIEW" subtitle="Authorized faculty case review · CSE · Semester 5 · 2026–27">
      <div className="space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link to={backPath} className="ui-button ui-button-ghost !min-h-9 !px-2 !text-xs"><Icon name="back" />Back to {backLabel}</Link>
          <div className="flex flex-wrap items-center gap-2">
            <span className="ui-status-chip border-slate-200 bg-white text-slate-600">Authorized faculty</span>
            <span className="ui-status-chip border-[#cbdcf1] bg-[#f4f8fd] text-brand-700">CSE · 2026–27 · Sem 5</span>
          </div>
        </div>

        <section className="ui-case-panel border-[#cfe0f8] bg-[linear-gradient(120deg,#ffffff_0%,#f7fbff_60%,#eaf3ff_100%)] p-5 md:p-7">
          <div className="grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-center">
            <div className="min-w-0">
              <p className="ui-eyebrow">Student academic support case</p>
              <h2 className="mt-2 break-words text-2xl font-extrabold tracking-tight text-[#18345f] md:text-3xl">{profile.student.student_name}</h2>
              <p className="mt-2 text-sm font-semibold text-slate-600">{profile.student.roll_number ?? profile.student.student_id} · {profile.student.section} · Semester {profile.student_metrics.semester} · {profile.student_metrics.academic_year}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <KeyValue label="Mentor" value={user?.role === "mentor" ? user.name : "Assigned CSE mentor"} />
                <KeyValue label="Student record" value={profile.student.roll_number ?? profile.student.student_id} />
                <KeyValue label="Current cycle" value={`${profile.student_metrics.academic_year} · Semester ${profile.student_metrics.semester}`} />
              </div>
            </div>
            <div className={`rounded-2xl border p-5 ${statusTone}`}>
              <p className="ui-key-label">Current case status</p>
              <p className="mt-2 text-3xl font-extrabold text-ink-900">{statusLabel}</p>
              <div className="mt-4 grid grid-cols-2 gap-4 border-t border-black/5 pt-4">
                <KeyValue label="Risk score" value={score100(profile.current_status.risk_score)} />
                <KeyValue label="Priority" value={score100(profile.current_status.priority_score)} />
              </div>
              <p className="mt-4 text-sm leading-5 text-slate-700">Primary concern: <strong>{primarySignal ? RISK_META[primarySignal.key]?.label ?? readableRiskType(primarySignal.key) : "No elevated risk"}</strong></p>
            </div>
          </div>
        </section>

        <section aria-labelledby="academic-snapshot">
          <SectionHeading eyebrow="Academic snapshot" title="Current position" description="Current academic measures" />
          <h2 id="academic-snapshot" className="sr-only">Current academic position</h2>
          <div className="mt-3 grid min-w-0 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <article className="ui-metric-card"><div className="ui-metric-icon border-[#d7e6fb] bg-[#edf4ff] text-brand-700"><span className="text-sm font-extrabold">G</span></div><div><p className="ui-metric-label">Current GPA</p><p className="ui-metric-value">{profile.student_metrics.current_gpa}</p><p className="ui-metric-detail">Configured threshold {profile.thresholds.gpa_threshold}</p></div></article>
            <article className="ui-metric-card"><div className="ui-metric-icon border-[#d7e6fb] bg-[#edf4ff] text-brand-700"><span className="text-sm font-extrabold">%</span></div><div><p className="ui-metric-label">Attendance</p><p className="ui-metric-value">{profile.student_metrics.attendance}%</p><p className="ui-metric-detail">Configured threshold {profile.thresholds.attendance_threshold}%</p></div></article>
            <article className="ui-metric-card"><div className="ui-metric-icon border-[#d7e6fb] bg-[#edf4ff] text-brand-700"><span className="text-sm font-extrabold">B</span></div><div><p className="ui-metric-label">Backlogs</p><p className="ui-metric-value">{profile.student_metrics.backlogs}</p><p className="ui-metric-detail">Current unresolved courses</p></div></article>
            <article className="ui-metric-card"><div className="ui-metric-icon border-[#d7e6fb] bg-[#edf4ff] text-brand-700"><span className="text-sm font-extrabold">A</span></div><div><p className="ui-metric-label">Assignment completion</p><p className="ui-metric-value">{profile.student_metrics.assignment_completion}%</p><p className="ui-metric-detail">Current submission consistency</p></div></article>
          </div>
        </section>

        <section aria-labelledby="risk-evidence">
          <SectionHeading eyebrow="Risk evidence" title="Why does this case need attention?" description="Risk, priority and supporting evidence" />
          <h2 id="risk-evidence" className="sr-only">Current risk evidence</h2>
          <div className="mt-3 space-y-3">
            {currentSignals.map(({ key, result, courseName }) => <RiskEvidenceRow key={`${key}-${courseName ?? "student"}`} title={RISK_META[key]?.label ?? readableRiskType(key)} note={RISK_META[key]?.description ?? "Current model signal."} result={result} evidence={evidenceFor(key, result, profile)} courseName={courseName} />)}
          </div>
        </section>

        <section className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,.75fr)]">
          <Card as="section" className="min-w-0 overflow-hidden p-5 md:p-6">
            <SectionHeading eyebrow="Faculty context" title="What may explain the academic signal?" description="Recorded observations and current context" action={<span className="ui-status-chip border-brand-100 bg-brand-50 text-brand-700">{profile.academic_context.observation_count} observation{profile.academic_context.observation_count === 1 ? "" : "s"}</span>} />
            {contextItems.length === 0 ? <div className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">No faculty observation is recorded for this case.</div> : <div className="mt-4 space-y-3">{contextItems.map((item) => <article key={item.observation_id} className="rounded-xl border border-slate-200 bg-white p-4"><div className="flex flex-wrap items-center justify-between gap-2"><span className="ui-status-chip border-[#cbdcf1] bg-[#f4f8fd] text-brand-700">{item.intent_label}</span><span className="text-[11px] font-medium text-slate-400">{item.observed_on}</span></div><p className="mt-3 break-words text-sm leading-6 text-slate-700">{item.observation_text}</p><div className="mt-3 grid gap-3 sm:grid-cols-3"><KeyValue label="System context" value={item.impact_area || item.intent_label} /><KeyValue label="Urgency" value={item.urgency} /><KeyValue label="Status" value={`${item.status}${item.follow_up_required ? " · Follow-up" : ""}`} /></div></article>)}</div>}
          </Card>

          <Card as="section" className="min-w-0 p-5 md:p-6">
            <SectionHeading eyebrow="Decision support" title="What should happen next?" description="Choose the next support action" />
            <div className="mt-4 space-y-3">
              {primarySignal ? <div className="rounded-xl border border-brand-100 bg-brand-50 p-4"><p className="ui-key-label text-brand-700">Primary concern</p><p className="mt-1 text-base font-extrabold text-ink-900">{RISK_META[primarySignal.key]?.label ?? readableRiskType(primarySignal.key)}</p><p className="mt-1 text-xs text-slate-600">Priority {Math.round(profile.current_status.priority_score)} / 100 · confidence {primarySignal.result.confidence}</p></div> : null}
              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4"><p className="ui-key-label">Recommended next step</p><p className="mt-2 text-sm font-semibold leading-6 text-slate-700">{primaryAction || "Review the current evidence, decide whether support is needed, and record the outcome in the case workflow."}</p></div>
              <div className="grid gap-2 sm:grid-cols-2"><Link to={backPath} className="ui-button ui-button-secondary w-full"><Icon name="back" />Return to queue</Link>{user?.role === "mentor" ? <a href="#what-if" className="ui-button ui-button-primary w-full">Explore a scenario</a> : null}</div>
            </div>
          </Card>
        </section>

        <section aria-labelledby="active-work">
          <SectionHeading eyebrow="Case work" title="Open support work" description="Active alerts and intervention work for this student" action={<span className="ui-status-chip border-slate-200 bg-white text-slate-600">{profile.case_management?.open_alerts ?? 0} open work item{(profile.case_management?.open_alerts ?? 0) === 1 ? "" : "s"}</span>} />
          <h2 id="active-work" className="sr-only">Active support actions</h2>
          {caseCompleted ? <div role="status" className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-800">Case completed and saved to the academic support record{profile.case_management?.completed_at ? ` · ${new Date(profile.case_management.completed_at).toLocaleString()}` : ""}.</div> : null}
          <div className="mt-3 flex justify-end">
            {user?.role === "mentor" ? <ActionButton variant="secondary" className="!min-h-9 !text-xs" disabled={completingAlertId === studentId || caseCompleted} onClick={() => setCompletionDialogOpen(true)}>{completingAlertId === studentId ? "Completing…" : caseCompleted ? "Case completed ✓" : "Mark case as complete"}</ActionButton> : null}
          </div>
          <div className="mt-3 space-y-3">
            {(profile.case_management?.items ?? []).length === 0 ? <div className="ui-case-panel p-5 text-sm text-slate-500">No active support work is recorded for this case.</div> : (profile.case_management?.items ?? []).map((item) => <article key={item.alert_id} className="ui-case-panel grid min-w-0 gap-4 p-4 md:grid-cols-[minmax(0,1.4fr)_140px_160px_auto] md:items-center"><div className="min-w-0"><p className="text-sm font-extrabold text-ink-900">{item.risk_label || readableRiskType(item.risk_type)}</p><p className="mt-1 text-xs leading-5 text-slate-500">{item.suggested_action || "Review the case and decide the appropriate support action."}</p></div><KeyValue label="Status" value={item.status === "NEW" ? "Open" : item.status.replaceAll("_", " ")} /><KeyValue label="Follow-up" value={item.follow_up_date || "Not scheduled"} /><div className="flex flex-wrap justify-end gap-2"><Link to={backPath} className="ui-button ui-button-secondary !min-h-9 !text-xs">Return to queue</Link>{user?.role === "mentor" && item.status !== "RESOLVED" ? <ActionButton variant="primary" className="!min-h-9 !text-xs" disabled={completingAlertId === studentId || caseCompleted} onClick={() => setCompletionDialogOpen(true)}>{completingAlertId === studentId ? "Completing…" : caseCompleted ? "Completed ✓" : "Mark as complete"}</ActionButton> : null}</div></article>)}
          </div>
        </section>

        <section aria-labelledby="course-review">
          <SectionHeading eyebrow="Course review" title="Course failure risk by subject" description="Review risk by course" />
          <h2 id="course-review" className="sr-only">Course failure risk by subject</h2>
          <div className="ui-table-shell mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-[760px] w-full border-collapse text-left text-sm"><thead className="bg-[#f5f8fc] text-[10px] font-extrabold uppercase tracking-[.12em] text-[#617188]"><tr><th className="border-b border-slate-200 px-4 py-3">Course</th><th className="border-b border-slate-200 px-4 py-3">Risk</th><th className="border-b border-slate-200 px-4 py-3">Priority</th><th className="border-b border-slate-200 px-4 py-3">Evidence</th></tr></thead><tbody className="divide-y divide-slate-100">{courseRisks.map((course) => <tr key={course.course_id} className="hover:bg-[#f8fbff]"><td className="px-4 py-4"><p className="font-bold text-ink-900">{course.course_name}</p><p className="mt-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">{course.course_id}</p></td><td className="px-4 py-4"><StatusChip level={riskLabel(course.risk_level)}>{percentage(course.risk_probability)} · {riskLabel(course.risk_level)}</StatusChip></td><td className="px-4 py-4 font-extrabold text-brand-700">{score100(course.priority_score ?? course.risk_score ?? course.risk_probability * 100)}</td><td className="max-w-[360px] px-4 py-4 text-xs leading-5 text-slate-600">{evidenceFor("course_failure", course, profile)}</td></tr>)}</tbody></table>
          </div>
          {courseRisks.length === 0 ? <SectionNote>No current course-failure prediction is available for this student.</SectionNote> : null}
        </section>

        {user?.role === "mentor" ? (
          <section id="what-if" className="scroll-mt-28" aria-labelledby="what-if-title">
            <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(340px,.85fr)]">
              <Card className="min-w-0 p-5 md:p-6">
                <SectionHeading eyebrow="What-If analysis" title="Test one measurable improvement" description="Test one change and compare the estimated outcome" />
                <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                  {([ ["attendance", "Attendance", "Recover overall attendance"], ["gpa", "GPA", "Improve current GPA"], ["backlog", "Backlogs", "Clear unresolved courses"], ["assignment", "Assignments", "Improve submissions"], ["course", "Course", "Improve one current subject"] ] as const).map(([value, label, hint]) => <button key={value} type="button" onClick={() => selectWhatIfMode(value)} className={`min-w-0 rounded-xl border p-3 text-left transition ${whatIfMode === value ? "border-brand-200 bg-brand-50 text-brand-800" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}><p className="text-xs font-extrabold">{label}</p><p className="mt-1 text-[11px] leading-4 text-slate-500">{hint}</p></button>)}
                </div>
                <form onSubmit={(event) => void handleWhatIf(event)} className="mt-4 space-y-4">
                  {whatIfMode !== "course" ? <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div className="min-w-0"><p id="what-if-title" className="text-sm font-extrabold text-ink-900">{modeConfig.label} improvement</p><p className="mt-1 text-xs leading-5 text-slate-500">Test one measurable change. The student's real record is never changed.</p></div><button type="button" onClick={setScenarioPreset} className="ui-button ui-button-secondary !min-h-9 !px-3 !text-xs">Use recommended target</button></div><div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-end"><div><p className="ui-key-label">Current value</p><p className="mt-1 text-xl font-extrabold text-ink-900">{modeConfig.current}{modeConfig.suffix}</p></div><div className="hidden pb-2 text-center text-slate-400 sm:block" aria-hidden="true">→</div><label className="grid gap-1.5 text-xs font-semibold text-slate-600">Target value<div className="flex min-w-0 items-center gap-2"><input required type="number" min={modeConfig.min} max={modeConfig.max} step={modeConfig.step} value={whatIfValue} onChange={(event) => setWhatIfValue(event.target.value)} className="ui-control min-w-0 flex-1" /><span className="text-sm font-bold text-slate-500">{modeConfig.suffix || "value"}</span></div></label></div><p className="mt-3 text-[11px] leading-5 text-slate-500">Recommended target is based on the configured academic threshold or a modest measurable improvement.</p></div> : <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div className="min-w-0"><p className="text-sm font-extrabold text-ink-900">Improve one current course</p><p className="mt-1 text-xs leading-5 text-slate-500">Choose one course and one factor so the result has a clear academic meaning.</p></div><button type="button" onClick={setScenarioPreset} disabled={!selectedCourse} className="ui-button ui-button-secondary !min-h-9 !px-3 !text-xs">Use recommended target</button></div><div className="mt-4 grid gap-3 sm:grid-cols-2"><label className="grid gap-1.5 text-xs font-semibold text-slate-600">Course<select required value={selectedCourse} onChange={(event) => { setSelectedCourse(event.target.value); setCourseValue(""); }} className="ui-control"><option value="">Choose a course</option>{courseRisks.map((course) => <option key={course.course_id} value={course.course_id}>{course.course_id} · {course.course_name}</option>)}</select></label><label className="grid gap-1.5 text-xs font-semibold text-slate-600">Improve this factor<select value={courseFactor} onChange={(event) => { setCourseFactor(event.target.value as typeof courseFactor); setCourseValue(""); }} className="ui-control"><option value="course_attendance_percentage">Course attendance</option><option value="internal_marks">Internal marks</option><option value="assignment_completion_rate">Assignment completion</option></select></label></div><div className="mt-3"><label className="grid gap-1.5 text-xs font-semibold text-slate-600">Target value<div className="flex min-w-0 items-center gap-2"><input required disabled={!selectedCourse} type="number" min={courseFactorMeta.min} max={courseFactorMeta.max} step={courseFactorMeta.step} value={courseValue} onChange={(event) => setCourseValue(event.target.value)} placeholder={selectedCourse ? "Set a target" : "Choose a course first"} className="ui-control min-w-0 flex-1 disabled:bg-slate-100" /><span className="text-sm font-bold text-slate-500">{courseFactorMeta.suffix}</span></div></label><p className="mt-2 text-[11px] text-slate-500">Current value: <strong className="text-slate-700">{selectedCourse ? `${courseFactorMeta.current ?? "—"}${courseFactorMeta.suffix}` : "—"}</strong></p></div></div>}
                  <ActionButton type="submit" disabled={simulating || (whatIfMode === "course" && !selectedCourse)}>{simulating ? "Calculating estimate…" : "See estimated impact"}</ActionButton>
                </form>
                {whatIf ? <div className="mt-4 rounded-xl border border-[#cfe0f8] bg-[#f5f9ff] p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="ui-eyebrow">Estimated impact</p><p className="mt-1 text-sm font-extrabold text-ink-900">Baseline vs simulated outcome</p></div><span className="ui-status-chip border-[#cfe0f8] bg-white text-brand-700">Simulation only · not saved</span></div><div className="mt-4 grid gap-3 sm:grid-cols-2"><div className="rounded-xl border border-slate-200 bg-white p-4"><p className="ui-key-label">Current</p><p className="mt-1 text-2xl font-extrabold text-ink-900">{riskLabel(whatIf.baseline.summary.risk_level)}</p><p className="mt-1 text-xs text-slate-500">Risk {Math.round(whatIf.baseline.summary.risk_score)}/100 · Priority {Math.round(whatIf.baseline.summary.priority_score)}/100</p></div><div className="rounded-xl border border-brand-100 bg-brand-50 p-4"><p className="ui-key-label">Simulated</p><p className="mt-1 text-2xl font-extrabold text-brand-800">{riskLabel(whatIf.simulated.summary.risk_level)}</p><p className="mt-1 text-xs text-slate-600">Risk {Math.round(whatIf.simulated.summary.risk_score)}/100 · Priority {Math.round(whatIf.simulated.summary.priority_score)}/100</p></div></div><div className="mt-3 rounded-xl border border-white bg-white p-4"><div className="grid gap-3 sm:grid-cols-3"><KeyValue label="Priority change" value={`${Math.round(whatIf.baseline.summary.priority_score)} → ${Math.round(whatIf.simulated.summary.priority_score)}`} /><KeyValue label="Risk status" value={`${riskLabel(whatIf.baseline.summary.risk_level)} → ${riskLabel(whatIf.simulated.summary.risk_level)}`} /><KeyValue label="Interpretation" value={whatIf.interpretation.improved ? "Estimated improvement" : "No clear improvement"} /></div></div><p className="mt-3 text-xs leading-5 text-slate-600">{whatIf.interpretation.warning}</p></div> : <SectionNote>No scenario has been run yet. Choose one factor, set a target, and view the estimated impact before deciding whether an intervention is appropriate.</SectionNote>}
              </Card>

              <Card className="min-w-0 p-5 md:p-6">
                <SectionHeading eyebrow="Mentor intelligence" title="AI Copilot" description="Optional guidance based on the case evidence" />
                <div className="mt-4 grid gap-2 sm:grid-cols-2"><ActionButton variant="secondary" disabled={copilotLoading} onClick={() => void handleCopilot("risk_summary")}>Explain current risk</ActionButton><ActionButton disabled={copilotLoading} onClick={() => void handleCopilot("intervention_plan")}>Recommend next action</ActionButton>{lastWhatIfPayload ? <ActionButton variant="secondary" disabled={copilotLoading} className="sm:col-span-2" onClick={() => void handleCopilot("what_if_explanation")}>Explain last scenario</ActionButton> : null}</div>
                <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-bold text-ink-900">AI explanation</p><p className="mt-1 text-xs leading-5 text-slate-600">Optional. The numerical estimate above is independent of the AI provider.</p></div><span className="ui-status-chip border-slate-200 bg-white text-slate-600">Optional</span></div><p className="mt-3 text-[11px] leading-5 text-slate-500">The numerical simulation works without AI. AI guidance appears when an approved provider is configured.</p></div>
                {copilotLoading ? <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4 text-xs font-semibold text-slate-600">Preparing grounded mentor guidance…</div> : null}
                {copilotError ? <div className="mt-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold leading-5 text-red-800">{copilotError}</div> : null}
                {copilot ? <div className="mt-3 space-y-3"><div className="rounded-xl border border-slate-200 bg-white p-4"><p className="ui-key-label">Explanation</p><p className="mt-2 text-sm leading-6 text-slate-700">{copilot.explanation}</p></div><div className="rounded-xl border border-slate-200 bg-slate-50 p-4"><p className="ui-key-label">Recommended actions</p><ul className="mt-2 space-y-2 text-xs leading-5 text-slate-700">{copilot.recommended_actions.map((action) => <li key={action} className="flex gap-2"><span className="font-bold text-brand-700">•</span><span>{action}</span></li>)}</ul></div>{copilot.cautions.length > 0 ? <div className="rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="ui-key-label text-amber-800">Cautions</p><ul className="mt-2 space-y-1 text-xs leading-5 text-amber-900">{copilot.cautions.map((item) => <li key={item}>• {item}</li>)}</ul></div> : null}</div> : null}
              </Card>
            </div>
          </section>
        ) : null}

        <section>
          <SectionHeading eyebrow="Context history" title="Academic context over time" description="Faculty context recorded over time" />
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{profile.academic_context.intent_distribution.map((item) => <div key={item.intent} className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-sm font-bold capitalize text-ink-900">{item.intent.replaceAll("_", " ")}</p><p className="mt-1 text-xs text-slate-500">{item.count} observation{item.count === 1 ? "" : "s"}</p></div>)}</div>
          {profile.academic_context.intent_distribution.length === 0 ? <SectionNote>No context categories are recorded yet.</SectionNote> : null}
        </section>
        {user?.role === "mentor" ? <CompleteCaseDialog open={completionDialogOpen} studentName={profile.student.student_name} saving={completingAlertId === studentId} onClose={() => setCompletionDialogOpen(false)} onConfirm={(payload) => void handleMarkComplete(payload)} /> : null}
      </div>
    </InstitutionalShell>
  );
}
