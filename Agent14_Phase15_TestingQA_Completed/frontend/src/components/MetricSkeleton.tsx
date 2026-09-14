export default function MetricSkeleton({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" aria-label={`${label} loading`} className="p-5">
      <div className="h-3 w-24 animate-pulse rounded bg-slate-200" />
      <div className="mt-3 h-9 w-16 animate-pulse rounded bg-slate-200" />
      <div className="mt-3 h-3 w-36 animate-pulse rounded bg-slate-100" />
    </div>
  );
}
