interface StatusDotProps {
  status: "active" | "idle" | "alert";
  label: string;
}

const COLORS = {
  active: "bg-status-active",
  idle: "bg-status-idle",
  alert: "bg-status-alert",
};

export default function StatusDot({ status, label }: StatusDotProps) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
      <span className={`h-2 w-2 rounded-full ${COLORS[status]}`} aria-hidden="true" />
      {label}
    </span>
  );
}
