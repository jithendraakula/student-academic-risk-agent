import api from "../services/api";

export type InstitutionalAIIntent =
  | "executive_summary"
  | "risk_analysis"
  | "mentor_workload"
  | "intervention_coverage"
  | "priority_review";

export interface InstitutionalAIResponse {
  role: "hod" | "dean";
  scope: string;
  intent: InstitutionalAIIntent;
  provider: string;
  model: string;
  grounded: boolean;
  title: string;
  executive_summary: string;
  key_findings: string[];
  recommended_actions: string[];
  cautions: string[];
  source_snapshot: {
    risk_source: string;
    risk_types: string[];
    scope: Record<string, string>;
  };
}

export async function runInstitutionalAI(intent: InstitutionalAIIntent, focus?: string) {
  const response = await api.post<InstitutionalAIResponse>("/institutional-ai/analyze", {
    intent,
    focus: focus?.trim() || undefined,
  });
  return response.data;
}
