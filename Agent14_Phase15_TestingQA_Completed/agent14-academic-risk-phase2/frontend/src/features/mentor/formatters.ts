export function riskPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function scorePercent(value: number) {
  return `${Math.round(value)}%`;
}

export function readableRiskType(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

export function riskTone(level: string) {
  const normalized = level.toUpperCase();
  if (normalized === "CRITICAL") return "text-red-700 bg-red-50 border-red-200";
  if (normalized === "HIGH") return "text-orange-700 bg-orange-50 border-orange-200";
  if (normalized === "MODERATE" || normalized === "MEDIUM") return "text-amber-700 bg-amber-50 border-amber-200";
  return "text-green-700 bg-green-50 border-green-200";
}
