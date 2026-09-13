import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle: string;
  badge?: ReactNode;
}

export default function PageHeader({ title, subtitle, badge }: Props) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-6 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs font-semibold tracking-widest text-brand-600">
              VIGNAN UNIVERSITY
            </p>

            <p className="mt-2 text-sm text-slate-600">
              Student Success Early Warning System
            </p>

            <h1 className="mt-2 text-3xl font-bold text-ink-900">
              {title}
            </h1>

            <p className="mt-1 text-slate-500">
              {subtitle}
            </p>
          </div>

          {badge && <div className="mt-2 flex-shrink-0">{badge}</div>}
        </div>
      </div>
    </header>
  );
}