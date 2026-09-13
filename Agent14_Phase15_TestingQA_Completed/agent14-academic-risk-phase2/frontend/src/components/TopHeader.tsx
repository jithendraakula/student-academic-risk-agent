interface TopHeaderProps {
  eyebrow: string;
  title: string;
}

export default function TopHeader({ eyebrow, title }: TopHeaderProps) {
  return (
    <header className="w-full bg-white border-b border-slate-100 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {/* Institutional logo placeholder - replace src with actual Vignan's logo asset */}
        <div className="w-9 h-9 rounded-md bg-brand-500 flex items-center justify-center text-white font-bold text-sm">
          V
        </div>
        <div className="text-xs font-semibold text-slate-400 tracking-wide leading-none">
          <div className="uppercase">Vignan's</div>
        </div>
      </div>

      <div className="text-center">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          {eyebrow}
        </div>
        <h1 className="text-lg font-bold text-ink-900">{title}</h1>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-400">
        {/* Accreditation badge row placeholder - swap in real badge assets */}
        <span className="px-2 py-1 rounded-full border border-slate-200">NAAC A+</span>
        <span className="px-2 py-1 rounded-full border border-slate-200">NBA</span>
      </div>
    </header>
  );
}
