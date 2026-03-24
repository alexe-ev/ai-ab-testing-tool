"use client";

import { useState } from "react";
import type { MergedCase, EvalDimensionScore } from "@/lib/types";

interface CaseViewerProps {
  case: MergedCase;
  promptAKey: string;
  promptBKey: string;
  promptAName: string;
  promptBName: string;
}

function scoreBadgeClass(score: number | null): string {
  if (score === null) return "bg-[#222] text-[#888] border-[#333]";
  if (score <= 2) return "bg-red-900 text-red-300 border-red-700";
  if (score === 3) return "bg-yellow-900 text-yellow-300 border-yellow-700";
  return "bg-green-900 text-green-300 border-green-700";
}

function DimensionScore({
  name,
  data,
}: {
  name: string;
  data: EvalDimensionScore;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-2">
      <div
        className="flex items-center gap-2 cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className="text-xs text-[#555]">{expanded ? "▾" : "▸"}</span>
        <span className="text-xs text-[#888]">{name}</span>
        <span
          className={`ml-auto px-1.5 py-0.5 text-xs font-semibold rounded border ${scoreBadgeClass(data.score)}`}
        >
          {data.score ?? "—"}
        </span>
      </div>
      {expanded && data.reasoning && (
        <p className="mt-1 ml-4 text-xs text-[#555] leading-relaxed">{data.reasoning}</p>
      )}
    </div>
  );
}

function PromptColumn({
  promptKey,
  promptName,
  c,
}: {
  promptKey: string;
  promptName: string;
  c: MergedCase;
}) {
  const resp = c.responses[promptKey];
  const pointwiseDims = c.pointwise?.[promptKey];

  return (
    <div className="border border-[#222] rounded-lg p-4 space-y-3">
      <p className="text-sm font-semibold text-[#ededed]">{promptName}</p>
      {resp ? (
        <>
          <pre className="text-xs text-[#ccc] whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
            {resp.response}
          </pre>
          <div className="text-xs text-[#555] flex gap-3">
            <span>{resp.model}</span>
            <span>{resp.latency_seconds.toFixed(2)}s</span>
            <span>{resp.input_tokens + resp.output_tokens} tokens</span>
          </div>
        </>
      ) : (
        <p className="text-xs text-[#555]">No response</p>
      )}
      {pointwiseDims && Object.keys(pointwiseDims).length > 0 && (
        <div className="border-t border-[#222] pt-3">
          {Object.entries(pointwiseDims).map(([dim, score]) => (
            <DimensionScore key={dim} name={dim} data={score} />
          ))}
        </div>
      )}
    </div>
  );
}

function PairwiseSection({ c, promptAName, promptBName }: { c: MergedCase; promptAName: string; promptBName: string }) {
  const pw = c.pairwise;
  const [showRound1, setShowRound1] = useState(false);
  const [showRound2, setShowRound2] = useState(false);

  if (!pw) return null;

  const winnerName = pw.winner === "prompt_a" || pw.winner === "a" ? promptAName : pw.winner === "tie" ? "TIE" : promptBName;
  const winnerBadgeClass =
    pw.winner === "prompt_a" || pw.winner === "a"
      ? "bg-blue-900 text-blue-300 border-blue-700"
      : pw.winner === "tie"
      ? "bg-[#222] text-[#888] border-[#333]"
      : "bg-purple-900 text-purple-300 border-purple-700";

  return (
    <div className="border border-[#222] rounded-lg p-4 space-y-3">
      <p className="text-sm font-semibold text-[#888]">Pairwise</p>
      <div className="flex items-center gap-3">
        <span className={`px-2 py-0.5 text-xs font-semibold rounded border ${winnerBadgeClass}`}>
          Winner: {winnerName}
        </span>
        <span
          className={`text-xs ${pw.consistent ? "text-green-400" : "text-yellow-400"}`}
        >
          {pw.consistent ? "Consistent" : "Inconsistent"}
        </span>
      </div>

      {pw.round1 && (
        <div>
          <div
            className="flex items-center gap-1 cursor-pointer select-none"
            onClick={() => setShowRound1((v) => !v)}
          >
            <span className="text-xs text-[#555]">{showRound1 ? "▾" : "▸"}</span>
            <span className="text-xs text-[#888]">Round 1 reasoning</span>
          </div>
          {showRound1 && (
            <p className="mt-1 ml-4 text-xs text-[#555] leading-relaxed">{pw.round1.reasoning}</p>
          )}
        </div>
      )}

      {pw.round2_swapped && (
        <div>
          <div
            className="flex items-center gap-1 cursor-pointer select-none"
            onClick={() => setShowRound2((v) => !v)}
          >
            <span className="text-xs text-[#555]">{showRound2 ? "▾" : "▸"}</span>
            <span className="text-xs text-[#888]">Round 2 (swapped) reasoning</span>
          </div>
          {showRound2 && (
            <p className="mt-1 ml-4 text-xs text-[#555] leading-relaxed">{pw.round2_swapped.reasoning}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function CaseViewer({
  case: c,
  promptAKey,
  promptBKey,
  promptAName,
  promptBName,
}: CaseViewerProps) {
  return (
    <div className="space-y-4">
      {/* Meta */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-[#555]">{c.test_case_id}</span>
        {c.category && (
          <span className="px-1.5 py-0.5 text-xs bg-[#111] border border-[#333] rounded text-[#666]">
            {c.category}
          </span>
        )}
        {c.skipped && (
          <span className="px-1.5 py-0.5 text-xs bg-yellow-900 border border-yellow-700 rounded text-yellow-300">
            skipped
          </span>
        )}
      </div>

      {/* Input */}
      <div className="border border-[#222] rounded-lg p-4 space-y-1">
        <p className="text-xs text-[#888] font-medium">User Input</p>
        <pre className="text-sm text-[#ccc] whitespace-pre-wrap leading-relaxed">{c.input}</pre>
      </div>

      {/* Context */}
      {c.context && (
        <div className="border border-[#222] rounded-lg p-4 space-y-1">
          <p className="text-xs text-[#888] font-medium">Context</p>
          <pre className="text-sm text-[#ccc] whitespace-pre-wrap leading-relaxed">{c.context}</pre>
        </div>
      )}

      {/* Side-by-side responses */}
      <div className="grid grid-cols-2 gap-4">
        <PromptColumn promptKey={promptAKey} promptName={promptAName} c={c} />
        <PromptColumn promptKey={promptBKey} promptName={promptBName} c={c} />
      </div>

      {/* Pairwise */}
      <PairwiseSection c={c} promptAName={promptAName} promptBName={promptBName} />
    </div>
  );
}
