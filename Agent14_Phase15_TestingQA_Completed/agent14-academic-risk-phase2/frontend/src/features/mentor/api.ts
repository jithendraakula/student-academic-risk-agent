import api from "../../services/api";

export type MentorAlertStatus = "NEW" | "ACKNOWLEDGED" | "ACTION_TAKEN" | "FOLLOW_UP" | "RESOLVED";

export interface MentorAlert {
  alert_id: string;
  student_id: string;
  student_name: string;
  teacher_id: string;
  risk_type: string;
  risk_label?: string;
  risk_score: number;
  priority_score: number;
  status: MentorAlertStatus;
  risk_level?: string;
  confidence?: string;
  intervenability_score?: number;
  course_id?: string | null;
  suggested_action?: string;
  created_at?: string;
  follow_up_date?: string;
}

export interface MentorStudentRow {
  student_id: string;
  student_name: string;
  department: string;
  batch: string;
  section: string;
  risk_score: number;
  priority_score: number;
  risk_level: string;
  critical: boolean;
  high_risk: boolean;
  needs_action: boolean;
  primary_risk: string | null;
  risk_types: string[];
  risk_scores: Record<string, number>;
  priority_scores: Record<string, number>;
  open_alerts: number;
  new_alerts: number;
  alerts: MentorAlert[];
  primary_alert: MentorAlert | null;
}

export interface MentorWorkspaceResponse {
  mentor_id: string;
  mentor_name: string;
  department?: string;
  assigned_students: number;
  critical_students: number;
  high_risk_students: number;
  students_needing_action: number;
  open_alerts: number;
  new_alerts: number;
  items: MentorStudentRow[];
  returned_students?: number;
  risk_source: string;
  alert_policy: { priority_threshold: number; critical_override: boolean };
}

export interface RiskResult {
  risk_probability: number;
  risk_score?: number;
  risk_level: "LOW" | "MODERATE" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: "LOW" | "MEDIUM" | "HIGH";
  intervenability_score?: number;
  priority_score?: number;
  top_factors: Array<{ feature: string; value: string | number | boolean | null; importance?: number }>;
}

export interface RiskProfileResponse {
  student: {
    student_id: string;
    student_name: string;
    department: string;
    batch: string;
    section: string;
  };
  student_id: string;
  thresholds: {
    gpa_threshold: number;
    attendance_threshold: number;
    current_gpa_below_threshold: boolean;
    projected_attendance_below_threshold: boolean;
    source: string;
  };
  student_metrics: {
    current_gpa: number;
    current_cgpa: number;
    attendance: number;
    backlogs: number;
    internal_marks: number;
    absence_rate: number;
  };
  risks: {
    course_failure: Array<RiskResult & { course_id: string; course_name: string }>;
    backlog: RiskResult;
    gpa_threshold: RiskResult;
    attendance_shortage: RiskResult;
    discontinuation: RiskResult;
  };
}

export async function getMentorWorkspace(params?: {
  q?: string;
  risk_type?: string;
  severity?: string;
  status?: string;
  needs_action?: boolean;
}) {
  const response = await api.get<MentorWorkspaceResponse>("/mentor/students", { params });
  return response.data;
}

export async function getMentorSummary() {
  const response = await api.get<Omit<MentorWorkspaceResponse, "items">>("/mentor/summary");
  return response.data;
}

export async function getWatchlist() {
  const response = await api.get<{ items: MentorAlert[]; assigned_students: number; open_alerts: number }>("/mentor/watchlist");
  return response.data;
}

export async function getAlerts() {
  const response = await api.get<{ items: MentorAlert[] }>("/mentor/alerts");
  return response.data.items;
}

export async function getRiskProfile(studentId: string) {
  const response = await api.get<RiskProfileResponse>(`/predictions/student/${studentId}`);
  return response.data;
}

export async function acknowledgeAlert(alertId: string) {
  const response = await api.post<MentorAlert>(`/mentor/alerts/${alertId}/acknowledge`);
  return response.data;
}

export async function updateIntervention(alertId: string, status: Exclude<MentorAlertStatus, "NEW">, notes: string, followUpDate?: string) {
  const response = await api.patch(`/interventions/${alertId}`, { status, notes, follow_up_date: followUpDate || null });
  return response.data as MentorAlert;
}

export interface WhatIfRequest {
  attendance_percentage?: number;
  gpa?: number;
  backlog_count?: number;
  assignment_completion_rate?: number;
  course?: {
    course_id: string;
    internal_marks?: number;
    midterm_marks?: number;
    quiz_average?: number;
    assignment_average?: number;
    practical_marks?: number;
    course_attendance_percentage?: number;
    assignment_completion_rate?: number;
  };
}

export interface WhatIfResponse {
  simulation: {
    persistent: boolean;
    source: string;
    semester: number;
    checkpoint_week: number;
    changes: Record<string, unknown>;
  };
  student: RiskProfileResponse["student"];
  baseline: { summary: { risk_score: number; priority_score: number; primary_risk: string | null; risk_level: string }; risks: RiskProfileResponse["risks"] };
  simulated: { summary: { risk_score: number; priority_score: number; primary_risk: string | null; risk_level: string }; risks: RiskProfileResponse["risks"] };
  changes: Record<string, { risk_score_delta: number; priority_score_delta: number; risk_level_changed: boolean }>;
  interpretation: { overall_priority_delta: number; improved: boolean; warning: string };
}

export async function runWhatIf(studentId: string, payload: WhatIfRequest) {
  const response = await api.post<WhatIfResponse>(`/what-if/student/${studentId}`, payload);
  return response.data;
}
