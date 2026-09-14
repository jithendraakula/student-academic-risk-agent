import api from "../../services/api";

export interface AdminStudent {
  student_id: string;
  student_name: string;
  roll_number?: string | null;
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

export async function getAdminStudents(params?: { q?: string; page?: number; page_size?: number }) { const response = await api.get<{ items: AdminStudent[]; total:number; page:number; page_size:number; total_pages:number }>("/admin/students", { params }); return response.data; }

export async function getAdminTeachers(params?: { q?: string; page?: number; page_size?: number }) { const response = await api.get<{ items: AdminTeacher[]; total:number; page:number; page_size:number; total_pages:number }>("/admin/teachers", { params }); return response.data; }

export async function getAdminConfig() {
  const response = await api.get<AdminConfig>("/admin/config");
  return response.data;
}

export async function updateAdminConfig(config: AdminConfig) {
  const response = await api.put<AdminConfig>("/admin/config", config);
  return response.data;
}


export interface AdminCaseSummary {
  open_cases: number;
  open_work_items: number;
  completed_cases: number;
  resolution_rate: number;
}

export async function getAdminCaseSummary() {
  const response = await api.get<AdminCaseSummary>("/admin/case-summary");
  return response.data;
}


export interface AdminAuditLog { id:number; actor_id?:string|null; action:string; resource_type?:string|null; resource_id?:string|null; ip_address?:string|null; details:Record<string, unknown>; created_at?:string|null }
export async function getAdminAuditLogs(params?: { q?: string; page?: number; page_size?: number }) { const response = await api.get<{items: AdminAuditLog[]; total:number; page:number; page_size:number; total_pages:number}>("/admin/audit-logs", { params }); return response.data; }
