import { useState } from "react";
import { ActionButton } from "./AcademicUI";

export interface CompletionPayload { action_category: string; completion_reason: string; notes: string; follow_up_outcome: string }

export default function CompleteCaseDialog({ open, studentName, saving, onClose, onConfirm }: { open: boolean; studentName: string; saving: boolean; onClose: () => void; onConfirm: (payload: CompletionPayload) => void }) {
  const [category, setCategory] = useState("GENERAL_SUPPORT");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState("");
  if (!open) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="dialog" aria-modal="true" aria-labelledby="complete-case-title">
    <div className="w-full max-w-lg rounded-2xl bg-white p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-4"><div><p className="ui-eyebrow">Case closure</p><h2 id="complete-case-title" className="mt-1 text-lg font-bold text-ink-900">Complete {studentName}'s support case</h2><p className="mt-1 text-xs leading-5 text-slate-500">Record what was done before closing the current case. This is saved to the academic support history.</p></div><button type="button" aria-label="Close" className="text-slate-400 hover:text-slate-700" onClick={onClose}>✕</button></div>
      <div className="mt-4 grid gap-3"><label className="grid gap-1.5 text-xs font-semibold text-slate-600">Action category<select value={category} onChange={e=>setCategory(e.target.value)} className="ui-control"><option value="GENERAL_SUPPORT">General support</option><option value="STUDENT_COUNSELLING">Student counselling</option><option value="ATTENDANCE_FOLLOW_UP">Attendance follow-up</option><option value="ACADEMIC_RECOVERY">Academic recovery plan</option><option value="PARENT_CONTACT">Parent/guardian contact</option><option value="FACULTY_COORDINATION">Faculty coordination</option><option value="REFERRAL">Referral / escalation</option></select></label>
      <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Completion reason<textarea value={reason} onChange={e=>setReason(e.target.value)} maxLength={255} rows={2} placeholder="Why is the current support action considered complete?" className="ui-control resize-y" /></label>
      <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Mentor notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} maxLength={2000} rows={3} required placeholder="Record the action taken and evidence." className="ui-control resize-y" /></label>
      <label className="grid gap-1.5 text-xs font-semibold text-slate-600">Follow-up outcome<textarea value={outcome} onChange={e=>setOutcome(e.target.value)} maxLength={128} rows={2} placeholder="Optional outcome or hand-off for the next review." className="ui-control resize-y" /></label></div>
      <div className="mt-5 flex justify-end gap-2"><ActionButton variant="ghost" onClick={onClose} disabled={saving}>Cancel</ActionButton><ActionButton variant="primary" disabled={saving || !notes.trim()} onClick={()=>onConfirm({action_category:category,completion_reason:reason,notes,follow_up_outcome:outcome})}>{saving ? "Saving…" : "Complete case"}</ActionButton></div>
    </div>
  </div>;
}
