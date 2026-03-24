"use client";

interface ScoreComparisonProps {
  overall: Record<string, number | string>;
  promptA: string;
  promptB: string;
}

// Rubric scale ceiling: levels are scored 1-5
const MAX_SCORE = 5.0;

export default function ScoreComparison({
  overall,
  promptA,
  promptB,
}: ScoreComparisonProps) {
  const scoreA = typeof overall[promptA] === "number" ? (overall[promptA] as number) : 0;
  const scoreB = typeof overall[promptB] === "number" ? (overall[promptB] as number) : 0;
  const winner = overall.better as string;

  const widthA = Math.round((scoreA / MAX_SCORE) * 100);
  const widthB = Math.round((scoreB / MAX_SCORE) * 100);

  function barColor(name: string) {
    return name === winner ? "bg-white" : "bg-[#555]";
  }

  function labelColor(name: string) {
    return name === winner ? "text-[#ededed]" : "text-[#666]";
  }

  return (
    <div className="p-5 border border-[#222] rounded-lg space-y-3">
      <p className="text-sm text-[#888] font-medium">Overall Score</p>

      {[
        { name: promptA, score: scoreA, width: widthA },
        { name: promptB, score: scoreB, width: widthB },
      ].map(({ name, score, width }) => (
        <div key={name} className="flex items-center gap-3">
          <span className={`w-28 text-sm shrink-0 ${labelColor(name)}`}>{name}</span>
          <div className="flex-1 bg-[#111] rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${barColor(name)}`}
              style={{ width: `${width}%` }}
            />
          </div>
          <span className={`w-10 text-sm text-right shrink-0 ${labelColor(name)}`}>
            {score.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}
