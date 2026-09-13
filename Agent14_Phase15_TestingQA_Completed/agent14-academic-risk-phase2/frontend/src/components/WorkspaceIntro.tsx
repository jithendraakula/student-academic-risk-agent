interface Props {
  role: "mentor" | "hod" | "dean" | "admin";
  name?: string;
  context?: string;
}

const COPY = {
  mentor: {
    label: "Mentor workspace",
    title: "Support the students who need you most",
    description: "Start with the students needing attention, open a case to understand why, then record the next support action.",
    question: "Today's mentor flow",
    steps: ["Review attention queue", "Open student case", "Record support action"],
  },
  hod: {
    label: "CSE department workspace",
    title: "Coordinate academic support across your department",
    description: "Start with department status, compare mentor support demand, then open the student cases that need departmental attention.",
    question: "HOD workflow",
    steps: ["Review department status", "Compare mentor load", "Open student case"],
  },
  dean: {
    label: "Institution workspace",
    title: "See where academic support is most needed",
    description: "Start with institutional priorities, identify departments needing attention, then review authorized cases and support coverage.",
    question: "Dean workflow",
    steps: ["Review institution", "Identify priority area", "Review authorized case"],
  },
  admin: {
    label: "System governance",
    title: "Keep academic risk operations configured correctly",
    description: "Manage verified authority records and academic risk policy settings that support the institutional workflow.",
    question: "Administration workflow",
    steps: ["Review configuration", "Review records", "Apply policy changes"],
  },
} as const;

export default function WorkspaceIntro({ role, name, context }: Props) {
  const copy = COPY[role];
  const title = role === "mentor" && name ? `${copy.title} · ${name}` : copy.title;

  return (
    <section className="relative overflow-hidden rounded-[22px] border border-[#cfe0f8] bg-gradient-to-r from-white via-[#f8fbff] to-[#eaf3ff] px-5 py-5 shadow-[0_10px_30px_rgba(30,58,95,0.06)] md:px-7 md:py-6">
      <div className="absolute -right-12 -top-20 h-48 w-48 rounded-full bg-[#dceaff]/70 blur-2xl" aria-hidden="true" />
      <div className="relative grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(420px,0.95fr)] lg:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#c6d9f4] bg-white/90 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-brand-700">{copy.label}</span>
            {context ? <span className="text-xs font-semibold text-slate-400">{context}</span> : null}
          </div>
          <h2 className="mt-2 text-xl font-extrabold tracking-tight text-[#18345f] md:text-2xl">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{copy.description}</p>
        </div>

        <div className="min-w-0 rounded-2xl border border-[#d7e3f2] bg-white/90 p-3 shadow-sm" aria-label={copy.question}>
          <p className="px-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{copy.question}</p>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            {copy.steps.map((step, index) => (
              <div key={step} className="min-w-0 rounded-xl border border-slate-100 bg-[#f8fbff] px-3 py-3">
                <div className="flex items-center gap-2">
                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[#edf4ff] text-[10px] font-extrabold text-brand-700">{index + 1}</span>
                  <span className="text-[11px] font-bold leading-4 text-ink-900">{step}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
