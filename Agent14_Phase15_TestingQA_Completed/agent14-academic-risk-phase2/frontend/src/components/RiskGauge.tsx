import { scoreToLevel, type RiskLevel } from "./RiskBadge";

interface RiskGaugeProps {
  score: number;
  label?: string;
  size?: "sm" | "md";
}

const COLORS: Record<RiskLevel, { ring: string; text: string }> = {
  critical: { ring: "#dc2626", text: "text-red-700" },
  high: { ring: "#ea580c", text: "text-orange-700" },
  medium: { ring: "#d97706", text: "text-amber-700" },
  low: { ring: "#16a34a", text: "text-green-700" },
};

const LABELS: Record<RiskLevel, string> = {
  critical: "Critical",
  high: "High",
  medium: "Moderate",
  low: "Low",
};

export default function RiskGauge({ score, label = "Risk score", size = "md" }: RiskGaugeProps) {
  const value = Math.max(0, Math.min(100, score));
  const level = scoreToLevel(value);
  const dimensions = size === "sm" ? "h-16 w-16" : "h-24 w-24";
  const inner = size === "sm" ? "inset-[5px]" : "inset-[7px]";

  return (
    <div className="inline-flex items-center gap-3" aria-label={`${label}: ${Math.round(value)} percent, ${LABELS[level]}`}>
      <div
        className={`relative shrink-0 rounded-full ${dimensions}`}
        style={{ background: `conic-gradient(${COLORS[level].ring} ${value * 3.6}deg, #e2e8f0 0deg)` }}
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(value)}
        aria-label={label}
      >
        <div className={`absolute ${inner} flex items-center justify-center rounded-full bg-white`}>
          <span className={`text-sm font-bold ${COLORS[level].text}`}>{Math.round(value)}%</span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-slate-500">{label}</p>
        <p className={`text-sm font-semibold ${COLORS[level].text}`}>{LABELS[level]}</p>
      </div>
    </div>
  );
}
