"use client";

import type { DimensionAnalysis, PromptDimensionStats } from "@/lib/types";

interface DimensionTableProps {
  dimensions: Record<string, DimensionAnalysis>;
  promptA: string;
  promptB: string;
}

function isPromptStats(val: unknown): val is PromptDimensionStats {
  return (
    typeof val === "object" &&
    val !== null &&
    "mean" in val &&
    "std" in val
  );
}

export default function DimensionTable({
  dimensions,
  promptA,
  promptB,
}: DimensionTableProps) {
  return (
    <div className="border border-[#222] rounded-lg overflow-hidden">
      <p className="px-4 py-3 text-sm text-[#888] font-medium border-b border-[#222]">
        Dimension Scores
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#222] text-[#666]">
              <th className="px-4 py-2 text-left font-normal">Dimension</th>
              <th className="px-4 py-2 text-right font-normal">Weight</th>
              <th className="px-4 py-2 text-right font-normal">{promptA}</th>
              <th className="px-4 py-2 text-right font-normal">{promptB}</th>
              <th className="px-4 py-2 text-right font-normal">Delta</th>
              <th className="px-4 py-2 text-right font-normal">p-value</th>
              <th className="px-4 py-2 text-right font-normal">Effect</th>
              <th className="px-4 py-2 text-right font-normal">Better</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(dimensions).map(([dimName, dim]) => {
              const statsA = dim[promptA];
              const statsB = dim[promptB];
              const comp = dim.comparison;

              const meanA = isPromptStats(statsA) ? statsA.mean : null;
              const stdA = isPromptStats(statsA) ? statsA.std : null;
              const meanB = isPromptStats(statsB) ? statsB.mean : null;
              const stdB = isPromptStats(statsB) ? statsB.std : null;

              const pValue = comp.ttest.p_value;
              const sig005 = comp.ttest.significant_005;
              const sig010 = comp.ttest.significant_010;

              let pLabel = pValue.toFixed(3);
              if (sig005) pLabel += " **";
              else if (sig010) pLabel += " *";

              const pColor = sig005
                ? "text-green-400"
                : sig010
                ? "text-yellow-400"
                : "text-[#888]";

              const betterColor =
                comp.better === promptA ? "text-blue-400" : "text-purple-400";

              return (
                <tr key={dimName} className="border-b border-[#111] hover:bg-[#0d0d0d]">
                  <td className="px-4 py-2 text-[#ededed]">{dimName}</td>
                  <td className="px-4 py-2 text-right text-[#888]">
                    {(dim.weight * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-2 text-right text-[#ededed]">
                    {meanA !== null ? meanA.toFixed(2) : "—"}
                    {stdA !== null ? (
                      <span className="text-[#555]"> ±{stdA.toFixed(2)}</span>
                    ) : null}
                  </td>
                  <td className="px-4 py-2 text-right text-[#ededed]">
                    {meanB !== null ? meanB.toFixed(2) : "—"}
                    {stdB !== null ? (
                      <span className="text-[#555]"> ±{stdB.toFixed(2)}</span>
                    ) : null}
                  </td>
                  <td className="px-4 py-2 text-right text-[#888]">
                    {comp.mean_diff > 0 ? "+" : ""}
                    {comp.mean_diff.toFixed(3)}
                  </td>
                  <td className={`px-4 py-2 text-right ${pColor}`}>{pLabel}</td>
                  <td className="px-4 py-2 text-right text-[#888]">
                    {comp.cohens_d.toFixed(2)}{" "}
                    <span className="text-[#555]">({comp.effect_interpretation})</span>
                  </td>
                  <td className={`px-4 py-2 text-right font-medium ${betterColor}`}>
                    {comp.better}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
