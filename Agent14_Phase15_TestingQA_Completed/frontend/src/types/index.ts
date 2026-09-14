export type Role = "mentor" | "hod" | "dean" | "admin";

export interface AuthUser {
  id: string;
  name: string;
  role: Role;
  department?: string;
}

export interface RiskProfile {
  studentId: string;
  studentName: string;
  courseFailureRisk: number; // 0-100, aggregate or per-course elsewhere
  backlogRisk: number;
  gpaThresholdRisk: number;
  attendanceRisk: number;
  supportAttentionRisk: number; // UI label for discontinuation risk
  overallPriority: number;
  confidence: "Low" | "Medium" | "High";
  intervenability: "Low" | "Medium" | "High";
  primaryRisk: string;
  topContributingFactors: string[];
  suggestedAction: string;
}

export interface CourseRisk {
  studentId: string;
  courseId: string;
  courseName: string;
  failureRiskScore: number;
}

export type AlertStatus =
  | "NEW"
  | "ACKNOWLEDGED"
  | "ACTION_TAKEN"
  | "FOLLOW_UP"
  | "RESOLVED";

export interface Alert {
  id: string;
  studentId: string;
  studentName: string;
  teacherId: string;
  riskType: string;
  riskScore: number;
  priorityScore: number;
  status: AlertStatus;
  createdAt: string;
  suggestedAction: string;
}

export interface MentorSummary {
  mentorId: string;
  mentorName: string;
  assignedStudents: number;
  criticalStudents: number;
  highRiskStudents: number;
  openAlerts: number;
  unacknowledgedAlerts: number;
  overdueFollowUps: number;
  interventionLoad: number;
}

export interface ModelMetrics {
  modelName: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  rocAuc: number;
}
