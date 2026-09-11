import api from "../../services/api";

export interface MentorComparisonRow {
  mentor_id: string;
  mentor_name: string;
  assigned_students: number;
  open_alerts: number;
  critical_students: number;
  high_risk_students: number;
  intervention_load: number;
}

export interface DepartmentStudent {
  student_id: string;
  student_name: string;
  batch: string;
  section: string;
  department: string;
}

export interface MentorStudent extends DepartmentStudent {
  risk_score: number;
  priority_score: number;
  high_risk: boolean;
  critical: boolean;
  open_alerts: number;
  risk_types: string[];
}

export async function getMentorComparison() {
  const response = await api.get<{ department: string; items: MentorComparisonRow[] }>("/hod/mentor-comparison");
  return response.data;
}

export async function getDepartmentStudents() {
  const response = await api.get<{ items: DepartmentStudent[] }>("/hod/students");
  return response.data.items;
}

export async function getMentorStudents(mentorId: string) {
  const response = await api.get<{ mentor_id: string; mentor_name: string; items: MentorStudent[] }>(`/hod/mentors/${mentorId}/students`);
  return response.data;
}
