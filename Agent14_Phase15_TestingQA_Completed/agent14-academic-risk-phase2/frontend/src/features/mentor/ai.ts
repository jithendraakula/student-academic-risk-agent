import api from "../../services/api";
import type { WhatIfRequest } from "./api";

export type CopilotIntent = "risk_summary" | "intervention_plan" | "what_if_explanation";

export interface CopilotResponse {
  student_id: string;
  intent: CopilotIntent;
  provider: string;
  model: string;
  grounded: boolean;
  explanation: string;
  recommended_actions: string[];
  priority_rationale: string;
  cautions: string[];
  source_snapshot: {
    risk_source: string;
    risk_types: string[];
    what_if_persistent?: boolean | null;
  };
}

export async function runMentorCopilot(studentId: string, intent: CopilotIntent, options?: {
  what_if?: WhatIfRequest;
  focus?: string;
}) {
  const response = await api.post<CopilotResponse>(`/mentor/ai/copilot/${studentId}`, {
    intent,
    what_if: options?.what_if,
    focus: options?.focus,
  });
  return response.data;
}
