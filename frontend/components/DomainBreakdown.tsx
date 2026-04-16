"use client";

import ScoreBar from "./ScoreBar";

const maxMap: Record<string, number> = {
  orientation_score: 10,
  registration_score: 3,
  attention_score: 5,
  recall_score: 3,
  language_score: 8,
  visuospatial_score: 1
};

export default function DomainBreakdown({ scores }: { scores: Record<string, number> }) {
  return (
    <div className="grid gap-3">
      {Object.entries(scores || {}).map(([k, v]) => (
        <div key={k}>
          <div className="flex justify-between text-sm mb-1">
            <span>{k.replace("_", " ")}</span>
            <span>{v}/{maxMap[k] ?? "?"}</span>
          </div>
          <ScoreBar score={v} max={maxMap[k] ?? 10} />
        </div>
      ))}
    </div>
  );
}
