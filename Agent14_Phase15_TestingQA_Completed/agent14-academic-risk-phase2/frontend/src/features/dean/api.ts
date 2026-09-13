import api from "../../services/api";

export interface DepartmentComparisonRow {
  department: string;
  total_students: number;
  critical_students: number;
  high_risk_students: number;
  students_needing_action: number;
  average_priority: number;
  active_interventions: number;
  resolved_interventions: number;
  new_alerts: number;
  support_attention_students: number;
  risk_counts: Record<string, number>;
}

export interface RiskHeatmapRow {
  department: string;
  attendance_shortage: number;
  course_failure: number;
  backlog: number;
  gpa_threshold: number;
  discontinuation: number;
}

export interface DeanStudent {
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
  risk_types: string[];
}

export interface DeanSummary {
  total_students: number;
  departments: number;
  critical_students: number;
  high_risk_students: number;
  high_only_students?: number;
  elevated_risk_students?: number;
  students_needing_action: number;
  students_with_multiple_risks?: number;
  risk_signals?: number;
  actionable_risk_signals?: number;
  support_attention_students: number;
  open_alerts: number;
  open_alert_students?: number;
  new_alerts: number;
  new_alert_students?: number;
  intervention_load: number;
  average_priority: number;
  risk_distribution: Array<{ risk_type: string; risk_label: string; affected_students: number; affected_rate: number; actionable_students: number; average_priority: number }>;
  metric_semantics?: Record<string, { meaning: string; unit: string }>;
  risk_thresholds?: { elevated: number; critical: number };
  alert_source?: string;
}

export interface PriorityQueueRow {
  student_id: string;
  student_name: string;
  roll_number?: string | null;
  department: string;
  batch: string;
  section: string;
  primary_risk: string | null;
  risk_score: number;
  priority_score: number;
  risk_level: string;
  critical: boolean;
  risk_types: string[];
}

export async function getDeanSummary() {
  const response = await api.get<DeanSummary>("/dean/summary");
  return response.data;
}

export async function getDepartmentComparison() {
  const response = await api.get<{ items: DepartmentComparisonRow[] }>("/dean/department-comparison");
  return response.data.items;
}

export async function getRiskHeatmap() {
  const response = await api.get<{ items: RiskHeatmapRow[] }>("/dean/risk-heatmap");
  return response.data.items;
}

export async function getPriorityQueue(limit = 12) {
  const response = await api.get<{ items: PriorityQueueRow[]; total_needing_action: number }>(`/dean/priority-queue?limit=${limit}`);
  return response.data;
}

export async function getDepartmentStudents(department: string) {
  const response = await api.get<{ department: string; items: DeanStudent[] }>(`/dean/departments/${encodeURIComponent(department)}/students`);
  return response.data;
}
