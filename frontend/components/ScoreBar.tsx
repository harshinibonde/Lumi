"use client";

export default function ScoreBar({ score, max }: { score: number; max: number }) {
  const pct = Math.max(0, Math.min(100, (score / Math.max(1, max)) * 100));
  return (
    <div className="w-full bg-slate-200 rounded-full h-3">
      <div className="h-3 rounded-full bg-brand-moss" style={{ width: `${pct}%` }} />
    </div>
  );
}
