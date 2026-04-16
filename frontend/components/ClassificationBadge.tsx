"use client";

const colors: Record<string, string> = {
  Normal: "bg-emerald-100 text-emerald-800",
  Mild: "bg-amber-100 text-amber-800",
  Moderate: "bg-orange-100 text-orange-800",
  Severe: "bg-rose-100 text-rose-800"
};

export default function ClassificationBadge({ label }: { label: string }) {
  const cls = colors[label] || "bg-slate-100 text-slate-800";
  return <span className={`px-3 py-1 rounded-full text-sm font-semibold ${cls}`}>{label}</span>;
}
