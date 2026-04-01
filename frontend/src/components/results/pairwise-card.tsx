"use client";

import type { PairwiseData } from "@/lib/types";
import Tooltip from "@/components/ui/tooltip";

interface PairwiseCardProps {
  pairwise: PairwiseData;
  promptA: string;
  promptB: string;
}

export default function PairwiseCard({ pairwise, promptA, promptB }: PairwiseCardProps) {
  const total = pairwise.total as number;
  const winsA = (pairwise[`wins_${promptA}`] as number) ?? 0;
  const winsB = (pairwise[`wins_${promptB}`] as number) ?? 0;
  const ties = (pairwise["ties"] as number) ?? 0;

  const pctA = total > 0 ? (winsA / total) * 100 : 0;
  const pctB = total > 0 ? (winsB / total) * 100 : 0;
  const pctTie = total > 0 ? (ties / total) * 100 : 0;

  const winRateA = pairwise[`win_rate_${promptA}`];
  const winRateB = pairwise[`win_rate_${promptB}`];
  const consistency = pairwise["swap_test_consistency"];

  const consistencyNum = typeof consistency === "number" ? consistency : null;
  const consistencyColor =
    consistencyNum === null
      ? "text-[#888]"
      : consistencyNum >= 0.8
      ? "text-green-400"
      : consistencyNum >= 0.6
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <div className="p-5 border border-[#222] rounded-lg space-y-4">
      <p className="text-sm text-[#888] font-medium">Pairwise Comparison</p>

      {/* Three-segment bar */}
      <div className="flex h-4 rounded-full overflow-hidden">
        <div
          className="bg-blue-600 transition-all"
          style={{ width: `${pctA}%` }}
          title={`${promptA}: ${winsA} wins`}
        />
        <div
          className="bg-[#333] transition-all"
          style={{ width: `${pctTie}%` }}
          title={`Ties: ${ties}`}
        />
        <div
          className="bg-purple-600 transition-all"
          style={{ width: `${pctB}%` }}
          title={`${promptB}: ${winsB} wins`}
        />
      </div>

      <div className="flex gap-4 text-xs text-[#888]">
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-blue-600" />
          {promptA}
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-[#333]" />
          Tie
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-purple-600" />
          {promptB}
        </span>
      </div>

      <div className="flex gap-6">
        <div>
          <p className="text-xs text-[#888] mb-0.5">Win rate {promptA}</p>
          <p className="text-[#ededed] font-semibold">
            {typeof winRateA === "number" ? `${(winRateA * 100).toFixed(0)}%` : "—"}
          </p>
        </div>
        <div>
          <p className="text-xs text-[#888] mb-0.5">Win rate {promptB}</p>
          <p className="text-[#ededed] font-semibold">
            {typeof winRateB === "number" ? `${(winRateB * 100).toFixed(0)}%` : "—"}
          </p>
        </div>
        <div>
          <Tooltip text="Pairwise comparison is run twice with A/B order swapped. 100% = same winner both times = no positional bias.">
            <span className="text-xs text-[#888]">Swap consistency</span>
          </Tooltip>
          <p className={`font-semibold ${consistencyColor}`}>
            {consistencyNum !== null ? `${(consistencyNum * 100).toFixed(0)}%` : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}
