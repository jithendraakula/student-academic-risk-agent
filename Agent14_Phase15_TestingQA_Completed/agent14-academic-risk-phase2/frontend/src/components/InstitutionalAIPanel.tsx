import { useState } from "react";
import Card from "./Card";
import { runInstitutionalAI, type InstitutionalAIIntent, type InstitutionalAIResponse } from "../features/institutionalAI";

interface Props { role: "hod" | "dean"; }

const HOD_INTENTS: Array<[InstitutionalAIIntent, string]> = [
  ["executive_summary", "Department briefing"],
  ["mentor_workload", "Mentor workload"],
  ["intervention_coverage", "Intervention coverage"],
];

const DEAN_INTENTS: Array<[InstitutionalAIIntent, string]> = [
  ["executive_summary", "Institution briefing"],
  ["risk_analysis", "Risk concentration"],
  ["intervention_coverage", "Intervention coverage"],
  ["priority_review", "Priority queue"],
];

export default function InstitutionalAIPanel({ role }: Props) {
  const [result, setResult] = useState<InstitutionalAIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [focus, setFocus] = useState("");
  const intents = role === "hod" ? HOD_INTENTS : DEAN_INTENTS;

  async function run(intent: InstitutionalAIIntent) {
    setLoading(true); setError(null);
    try { setResult(await runInstitutionalAI(intent, focus)); }
    catch (requestError: any) { setError(requestError?.response?.data?.detail || "Institutional AI is unavailable. Configure the backend AI provider and API key."); }
    finally { setLoading(false); }
  }

  return (
    <Card as="section" className="overflow-hidden p-0">
      <div className="relative overflow-hidden border-b border-[#cadcf2] bg-gradient-to-r from-[#eef5fd] via-white to-[#f8fbff] px-5 py-5 md:px-6">
        <div className="absolute -right-8 -top-12 h-28 w-28 rounded-full bg-[#dceaff] blur-2xl" aria-hidden="true" />
        <div className="relative flex items-start gap-3">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#245f9f] text-base font-extrabold text-white shadow-sm">AI</div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-brand-700">Grounded academic AI</p>
            <h2 className="mt-1 text-lg font-extrabold text-[#18345f]">{role === "hod" ? "Department Risk Analyst" : "Institutional Risk Analyst"}</h2>
            <p className="mt-1 max-w-4xl text-xs leading-5 text-slate-600">The analyst interprets canonical ML and priority outputs. It does not calculate, overwrite, or invent institutional statistics.</p>
          </div>
        </div>
      </div>
      <div className="space-y-4 p-5 md:p-6">
        <div className="flex flex-wrap gap-2">
          {intents.map(([intent, label]) => <button key={intent} type="button" onClick={() => void run(intent)} disabled={loading} className="rounded-xl border border-[#cbd8e7] bg-white px-3 py-2 text-xs font-bold text-[#3b506a] transition hover:border-[#9ab9dd] hover:bg-[#f5f9ff] hover:text-brand-700 disabled:opacity-60">{loading ? "Analyzing…" : label}</button>)}
        </div>
        <label className="block text-xs font-bold text-slate-600">Optional focus
          <input value={focus} onChange={(event) => setFocus(event.target.value)} maxLength={300} placeholder="e.g. attendance recovery, mentor workload, backlog concentration" className="mt-1.5 w-full rounded-xl border border-slate-200 bg-[#fbfcfe] px-3 py-2.5 text-sm text-ink-900 outline-none transition focus:border-brand-400 focus:bg-white" />
        </label>
        {error ? <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {result ? (
          <div className="rounded-2xl border border-[#d5e2f0] bg-[#fbfdff] p-4 md:p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div><p className="text-xs font-extrabold uppercase tracking-[0.1em] text-brand-700">{result.title}</p><p className="mt-1 text-[10px] font-medium text-slate-400">{result.provider} · {result.model} · {result.grounded ? "grounded in canonical data" : "ungrounded"}</p></div>
              <span className="rounded-full border border-[#c9daee] bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-brand-700">AI brief</span>
            </div>
            <p className="mt-4 text-sm leading-6 text-ink-700">{result.executive_summary}</p>
            {result.key_findings.length > 0 ? <div className="mt-5"><p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">Key findings</p><ul className="mt-2 space-y-2 text-sm text-ink-700">{result.key_findings.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />{item}</li>)}</ul></div> : null}
            {result.recommended_actions.length > 0 ? <div className="mt-5"><p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">Recommended actions</p><ul className="mt-2 space-y-2 text-sm text-ink-700">{result.recommended_actions.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />{item}</li>)}</ul></div> : null}
            {result.cautions.length > 0 ? <div className="mt-5 border-t border-slate-200 pt-4"><p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500">Cautions</p><ul className="mt-2 space-y-1 text-xs leading-5 text-slate-600">{result.cautions.map((item) => <li key={item}>• {item}</li>)}</ul></div> : null}
          </div>
        ) : <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-4 py-5 text-center text-xs text-slate-500">Choose an analyst action to generate a grounded briefing from the current canonical data.</div>}
      </div>
    </Card>
  );
}
