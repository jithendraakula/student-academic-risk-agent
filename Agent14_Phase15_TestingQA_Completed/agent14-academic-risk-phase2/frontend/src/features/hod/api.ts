import api from "../../services/api";

export interface MentorComparisonRow {
  mentor_id: string;
  mentor_name: string;
  department: string;
  sections?: string[];
  assigned_students: number;
  critical_students: number;
  high_risk_students: number;
  high_only_students?: number;
  elevated_risk_students?: number;
  students_needing_action: number;
  students_with_multiple_risks?: number;
  risk_signals?: number;
  actionable_risk_signals?: number;
  open_alerts: number;
  open_alert_students?: number;
  completed_cases?: number;
  new_alerts: number;
  new_alert_students?: number;
  intervention_load: number;
  action_rate: number;
}

export interface RiskOverviewRow {
  risk_type: string;
  risk_label: string;
  affected_students: number;
  affected_rate: number;
  average_priority: number;
}

export interface HodSummary {
  department: string;
  total_students: number;
  total_mentors: number;
  critical_students: number;
  high_risk_students: number;
  high_only_students?: number;
  elevated_risk_students?: number;
  students_needing_action: number;
  students_with_multiple_risks?: number;
  risk_signals?: number;
  actionable_risk_signals?: number;
  open_alerts: number;
  open_alert_students?: number;
  new_alerts: number;
  new_alert_students?: number;
  intervention_load: number;
  support_attention_students: number;
  average_priority: number;
  risk_distribution: RiskOverviewRow[];
  metric_semantics?: Record<string, { meaning: string; unit: string }>;
  risk_thresholds?: { elevated: number; critical: number };
  alert_source?: string;
}

export interface DepartmentStudent {
  student_id: string;
  student_name: string;
  roll_number?: string | null;
  batch: string;
  section: string;
  department: string;
  risk_score: number;
  priority_score: number;
  risk_level: string;
  primary_risk: string | null;
  needs_action: boolean;
}

export interface MentorStudent extends DepartmentStudent {
  high_risk: boolean;
  critical: boolean;
  open_alerts: number;
  risk_types: string[];
  actionable_risk_types?: string[];
  risk_breakdown?: Array<{ risk_type: string; risk_label: string; risk_level: string; risk_score: number; priority_score: number; actionable: boolean; elevated: boolean; course_ids: string[] }>;
}

export async function getHodSummary() {
  const response = await api.get<HodSummary>("/hod/summary");
  return response.data;
}

export async function getRiskOverview() {
  const response = await api.get<{ department: string; items: RiskOverviewRow[] }>("/hod/risk-overview");
  return response.data;
}

export async function getMentorComparison() {
  const response = await api.get<{ department: string; items: MentorComparisonRow[] }>("/hod/mentor-comparison");
  return response.data;
}

export async function getDepartmentStudents() {
  const response = await api.get<{ department: string; items: DepartmentStudent[] }>("/hod/students");
  return response.data;
}

export async function getMentorStudents(mentorId: string, params?: { q?: string; section?: string; risk_type?: string; needs_action?: boolean }) {
  const response = await api.get<{ mentor_id: string; mentor_name: string; department: string; sections: string[]; items: MentorStudent[] }>(`/hod/mentors/${mentorId}/students`, { params });
  return response.data;
}
