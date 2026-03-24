"use client";

import type { Recommendation, PairwiseData } from "@/lib/types";

interface SummaryCardProps {
  recommendation: Recommendation;
  pairwise: PairwiseData;
  overall: Record<string, number | string>;
  promptA: string;
  promptB: string;
}

export default function SummaryCard({
  recommendation,
  pairwise,
  overall,
  promptA,
  promptB,
}: SummaryCardProps) {
  const { winner, confidence } = recommendation;

  const confidenceColor =
    confidence === "high"
      ? "bg-green-900 text-green-300 border-green-700"
      : confidence === "medium"
      ? "bg-yellow-900 text-yellow-300 border-yellow-700"
      : "bg-red-900 text-red-300 border-red-700";

  const winRateKey = `win_rate_${winner}`;
  const winRate = pairwise[winRateKey];
  const winRateStr =
    typeof winRate === "number" ? `${(winRate * 100).toFixed(0)}%` : "—";

  const scoreA = overall[promptA];
  const scoreB = overall[promptB];

  return (
    <div className="p-5 border border-[#222] rounded-lg space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#888]">Winner</span>
        <span className="px-3 py-1 bg-white text-black text-sm font-semibold rounded">
          {winner}
        </span>
        <span
          className={`px-2 py-0.5 text-xs rounded border font-medium ${confidenceColor}`}
        >
          {confidence} confidence
        </span>
      </div>

      <div className="flex gap-6">
        <div>
          <p className="text-xs text-[#888] mb-0.5">{promptA} score</p>
          <p className="text-lg font-semibold text-[#ededed]">
            {typeof scoreA === "number" ? scoreA.toFixed(2) : "—"}
          </p>
        </div>
        <div>
          <p className="text-xs text-[#888] mb-0.5">{promptB} score</p>
          <p className="text-lg font-semibold text-[#ededed]">
            {typeof scoreB === "number" ? scoreB.toFixed(2) : "—"}
          </p>
        </div>
        <div>
          <p className="text-xs text-[#888] mb-0.5">Win rate ({winner})</p>
          <p className="text-lg font-semibold text-[#ededed]">{winRateStr}</p>
        </div>
      </div>
    </div>
  );
}
