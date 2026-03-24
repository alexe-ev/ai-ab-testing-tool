"use client";

import type { NotableCase } from "@/lib/types";

interface NotableCasesProps {
  cases: Record<string, NotableCase[]>;
  promptA: string;
  promptB: string;
}

function CaseCard({ c }: { c: NotableCase }) {
  return (
    <div className="p-3 border border-[#222] rounded-lg space-y-1.5">
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-[#888]">{c.test_case_id}</span>
        {c.category && (
          <span className="px-1.5 py-0.5 text-xs bg-[#111] border border-[#333] rounded text-[#666]">
            {c.category}
          </span>
        )}
        <span className="ml-auto text-xs text-[#888]">
          delta: {c.mean_delta > 0 ? "+" : ""}
          {c.mean_delta.toFixed(2)}
        </span>
      </div>
      <p className="text-xs text-[#888] line-clamp-2">{c.input}</p>
    </div>
  );
}

export default function NotableCases({ cases, promptA, promptB }: NotableCasesProps) {
  const keyA = `best_for_${promptA}`;
  const keyB = `best_for_${promptB}`;
  const casesForA = cases[keyA] ?? [];
  const casesForB = cases[keyB] ?? [];

  if (casesForA.length === 0 && casesForB.length === 0) return null;

  return (
    <div className="border border-[#222] rounded-lg overflow-hidden">
      <p className="px-4 py-3 text-sm text-[#888] font-medium border-b border-[#222]">
        Notable Cases
      </p>
      <div className="grid grid-cols-2 divide-x divide-[#222]">
        <div className="p-4 space-y-2">
          <p className="text-xs text-[#888] mb-2">Best for {promptA}</p>
          {casesForA.length === 0 ? (
            <p className="text-xs text-[#555]">None</p>
          ) : (
            casesForA.map((c) => <CaseCard key={c.test_case_id} c={c} />)
          )}
        </div>
        <div className="p-4 space-y-2">
          <p className="text-xs text-[#888] mb-2">Best for {promptB}</p>
          {casesForB.length === 0 ? (
            <p className="text-xs text-[#555]">None</p>
          ) : (
            casesForB.map((c) => <CaseCard key={c.test_case_id} c={c} />)
          )}
        </div>
      </div>
    </div>
  );
}
