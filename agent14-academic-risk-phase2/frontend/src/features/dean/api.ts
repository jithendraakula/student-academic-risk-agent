import api from "../../services/api";

export interface DepartmentComparisonRow {
  department: string;
  total_students: number;
  critical_students: number;
  high_risk_students: number;
  average_priority: number;
  active_interventions: number;
  resolved_interventions: number;
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
  batch: string;
  section: string;
  department: string;
}

export async function getDepartmentComparison() {
  const response = await api.get<{ items: DepartmentComparisonRow[] }>("/dean/department-comparison");
  return response.data.items;
}

export async function getRiskHeatmap() {
  const response = await api.get<{ items: RiskHeatmapRow[] }>("/dean/risk-heatmap");
  return response.data.items;
}

export async function getDepartmentStudents(department: string) {
  const response = await api.get<{ department: string; items: DeanStudent[] }>(`/dean/departments/${department}/students`);
  return response.data;
}
