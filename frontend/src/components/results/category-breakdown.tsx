"use client";

import type { CategoryBreakdownEntry } from "@/lib/types";

interface CategoryBreakdownProps {
  categories: Record<string, CategoryBreakdownEntry>;
  promptA: string;
  promptB: string;
  overallWinner: string;
}

export default function CategoryBreakdown({
  categories,
  promptA,
  promptB,
  overallWinner,
}: CategoryBreakdownProps) {
  const entries = Object.entries(categories);
  if (entries.length === 0) return null;

  return (
    <div className="border border-[#222] rounded-lg overflow-hidden">
      <p className="px-4 py-3 text-sm text-[#888] font-medium border-b border-[#222]">
        Category Breakdown
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#222] text-[#666]">
              <th className="px-4 py-2 text-left font-normal">Category</th>
              <th className="px-4 py-2 text-right font-normal">Cases</th>
              <th className="px-4 py-2 text-right font-normal">{promptA}</th>
              <th className="px-4 py-2 text-right font-normal">{promptB}</th>
              <th className="px-4 py-2 text-right font-normal">Better</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([category, entry]) => {
              const isSplit = entry.better !== overallWinner;
              const scoreA = entry[promptA];
              const scoreB = entry[promptB];
              const betterColor =
                entry.better === promptA ? "text-blue-400" : "text-purple-400";

              return (
                <tr
                  key={category}
                  className={[
                    "border-b border-[#111]",
                    isSplit ? "bg-yellow-950/30 border-l-2 border-l-yellow-700" : "hover:bg-[#0d0d0d]",
                  ].join(" ")}
                >
                  <td className="px-4 py-2 text-[#ededed]">{category}</td>
                  <td className="px-4 py-2 text-right text-[#888]">{entry.n_cases}</td>
                  <td className="px-4 py-2 text-right text-[#ededed]">
                    {typeof scoreA === "number" ? scoreA.toFixed(2) : "—"}
                  </td>
                  <td className="px-4 py-2 text-right text-[#ededed]">
                    {typeof scoreB === "number" ? scoreB.toFixed(2) : "—"}
                  </td>
                  <td className={`px-4 py-2 text-right font-medium ${betterColor}`}>
                    {entry.better}
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
