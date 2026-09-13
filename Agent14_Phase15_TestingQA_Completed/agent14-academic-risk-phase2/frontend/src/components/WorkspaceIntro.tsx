interface Props {
  role: "mentor" | "hod" | "dean" | "admin";
  name?: string;
  context?: string;
}

const COPY = {
  mentor: {
    label: "Mentor desk",
    title: "Student support at a glance",
    description: "Prioritize assigned students, understand the evidence behind each signal, and record the next mentor action.",
  },
  hod: {
    label: "Department office",
    title: "Turn risk patterns into department action",
    description: "Compare mentor support load, focus on students needing attention, and coordinate interventions across your department.",
  },
  dean: {
    label: "Institution office",
    title: "Institution-wide academic early warning",
    description: "See concentration, priority, and intervention coverage across academic units without replacing human judgment.",
  },
  admin: {
    label: "System governance",
    title: "Keep academic risk operations configured correctly",
    description: "Manage institutional records and policy thresholds that support the academic early-warning workflow.",
  },
} as const;

export default function WorkspaceIntro({ role, name, context }: Props) {
  const copy = COPY[role];
  return (
    <section className="relative overflow-hidden rounded-[22px] border border-[#cfe0f8] bg-gradient-to-r from-white via-[#f8fbff] to-[#eaf3ff] px-5 py-5 shadow-[0_10px_30px_rgba(30,58,95,0.06)] md:px-7 md:py-6">
      <div className="absolute -right-12 -top-20 h-48 w-48 rounded-full bg-[#dceaff]/70 blur-2xl" aria-hidden="true" />
      <div className="absolute bottom-0 left-1/2 h-px w-2/3 bg-gradient-to-r from-transparent via-[#bad2f1] to-transparent" aria-hidden="true" />
      <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#c6d9f4] bg-white/85 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-brand-700">{copy.label}</span>
            {context ? <span className="text-xs font-semibold text-slate-400">{context}</span> : null}
          </div>
          <h2 className="mt-2 text-xl font-extrabold tracking-tight text-[#18345f] md:text-2xl">{copy.title}{role === "mentor" && name ? ` · ${name}` : ""}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{copy.description}</p>
        </div>
        <div className="grid shrink-0 grid-cols-3 overflow-hidden rounded-2xl border border-[#d7e3f2] bg-white/85 text-center shadow-sm">
          <div className="px-4 py-3"><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">ML</p><p className="mt-1 text-xs font-bold text-ink-900">Predict</p></div>
          <div className="border-x border-slate-100 px-4 py-3"><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Priority</p><p className="mt-1 text-xs font-bold text-ink-900">Act</p></div>
          <div className="px-4 py-3"><p className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Mentor</p><p className="mt-1 text-xs font-bold text-ink-900">Support</p></div>
        </div>
      </div>
    </section>
  );
}