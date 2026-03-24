"use client";

import { diffChars, Change } from "diff";

interface DiffViewerProps {
  textA: string;
  textB: string;
  labelA?: string;
  labelB?: string;
}

export default function DiffViewer({
  textA,
  textB,
  labelA = "Prompt A",
  labelB = "Prompt B",
}: DiffViewerProps) {
  const changes: Change[] = diffChars(textA, textB);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-4 text-xs text-[#666]">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-red-900/60 border border-red-700/50" />
          Removed ({labelA})
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-green-900/60 border border-green-700/50" />
          Added ({labelB})
        </span>
      </div>
      <div
        className="bg-[#111] border border-[#333] rounded p-4 text-sm font-mono whitespace-pre-wrap break-words leading-relaxed"
        style={{ fontFamily: "var(--font-geist-mono)" }}
      >
        {changes.map((part, i) => {
          if (part.removed) {
            return (
              <span
                key={i}
                className="bg-red-900/40 text-red-300 rounded-sm"
              >
                {part.value}
              </span>
            );
          }
          if (part.added) {
            return (
              <span
                key={i}
                className="bg-green-900/40 text-green-300 rounded-sm"
              >
                {part.value}
              </span>
            );
          }
          return <span key={i} className="text-[#ededed]">{part.value}</span>;
        })}
      </div>
    </div>
  );
}
