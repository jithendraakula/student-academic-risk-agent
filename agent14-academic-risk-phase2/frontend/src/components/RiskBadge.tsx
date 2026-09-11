export type RiskLevel = "critical" | "high" | "medium" | "low";

const STYLES: Record<RiskLevel, string> = {
  critical: "bg-red-50 text-red-600 border-red-200",
  high: "bg-orange-50 text-orange-600 border-orange-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  low: "bg-green-50 text-green-600 border-green-200",
};

const LABELS: Record<RiskLevel, string> = {
  critical: "Critical",
  high: "High Risk",
  medium: "Moderate",
  low: "Low Risk",
};

export function scoreToLevel(score: number): RiskLevel {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "medium";
  return "low";
}

export default function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide border ${STYLES[level]}`}
      aria-label={`Risk level: ${LABELS[level]}`}
    >
      {LABELS[level]}
    </span>
  );
}
