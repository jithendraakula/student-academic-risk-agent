import api from "../../services/api";

export interface MentorAlert {
  alert_id: string;
  student_id: string;
  student_name: string;
  teacher_id: string;
  risk_type: string;
  risk_score: number;
  priority_score: number;
  status: "NEW" | "ACKNOWLEDGED" | "ACTION_TAKEN" | "FOLLOW_UP" | "RESOLVED";
  suggested_action?: string;
  created_at?: string;
  intervention_type?: string;
  follow_up_date?: string;
}

export interface WatchlistResponse {
  items: MentorAlert[];
  assigned_students: number;
  open_alerts: number;
}

export interface RiskResult {
  risk_probability: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  confidence: "LOW" | "MEDIUM" | "HIGH";
  top_factors: Array<{ feature: string; value: string | number | boolean | null; importance: number }>;
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
  risks: {
    course_failure: Array<RiskResult & { course_id: string; course_name: string }>;
    backlog: RiskResult;
    gpa_threshold: RiskResult;
    attendance_shortage: RiskResult;
    discontinuation: RiskResult;
  };
}

export async function getWatchlist() {
  const response = await api.get<WatchlistResponse>("/mentor/watchlist");
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

export async function updateIntervention(alertId: string, status: Exclude<MentorAlert["status"], "NEW">, notes: string) {
  const response = await api.patch(`/interventions/${alertId}`, { status, notes });
  return response.data;
}
