import api from "../../services/api";

export interface MentorComparisonRow {
  mentor_id: string;
  mentor_name: string;
  department: string;
  assigned_students: number;
  critical_students: number;
  high_risk_students: number;
  students_needing_action: number;
  open_alerts: number;
  new_alerts: number;
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
  students_needing_action: number;
  open_alerts: number;
  new_alerts: number;
  intervention_load: number;
  support_attention_students: number;
  average_priority: number;
  risk_distribution: RiskOverviewRow[];
}

export interface DepartmentStudent {
  student_id: string;
  student_name: string;
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
  const response = await api.get<{ mentor_id: string; mentor_name: string; department: string; items: MentorStudent[] }>(`/hod/mentors/${mentorId}/students`, { params });
  return response.data;
}
