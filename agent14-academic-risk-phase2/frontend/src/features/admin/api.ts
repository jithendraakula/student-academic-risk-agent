import api from "../../services/api";

export interface AdminStudent {
  student_id: string;
  student_name: string;
  department: string;
  batch: string;
  section: string;
}

export interface AdminTeacher {
  teacher_id: string;
  teacher_name: string;
  role: string;
  department?: string;
  email: string;
}

export interface AdminConfig {
  gpa_threshold: number;
  attendance_threshold: number;
}

export async function getAdminStudents() {
  const response = await api.get<{ items: AdminStudent[] }>("/admin/students");
  return response.data.items;
}

export async function getAdminTeachers() {
  const response = await api.get<{ items: AdminTeacher[] }>("/admin/teachers");
  return response.data.items;
}

export async function getAdminConfig() {
  const response = await api.get<AdminConfig>("/admin/config");
  return response.data;
}

export async function updateAdminConfig(config: AdminConfig) {
  const response = await api.put<AdminConfig>("/admin/config", config);
  return response.data;
}
