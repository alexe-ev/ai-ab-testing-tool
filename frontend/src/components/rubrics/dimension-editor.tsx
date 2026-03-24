"use client";

import { useState } from "react";
import type { RubricDimensionFormData } from "@/lib/types";

interface DimensionEditorProps {
  dimension: RubricDimensionFormData;
  index: number;
  total: number;
  onChange: (updated: RubricDimensionFormData) => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}

export default function DimensionEditor({
  dimension,
  index,
  total,
  onChange,
  onDelete,
  onMoveUp,
  onMoveDown,
}: DimensionEditorProps) {
  const [expanded, setExpanded] = useState(true);

  function updateField<K extends keyof RubricDimensionFormData>(
    key: K,
    value: RubricDimensionFormData[K]
  ) {
    onChange({ ...dimension, [key]: value });
  }

  function updateLevel(levelIndex: number, description: string) {
    const levels = dimension.levels.map((l, i) =>
      i === levelIndex ? { ...l, description } : l
    );
    onChange({ ...dimension, levels });
  }

  return (
    <div className="border border-[#222] rounded-lg overflow-hidden">
      {/* Header */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => setExpanded((prev) => !prev)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") setExpanded((prev) => !prev);
        }}
        className="flex items-center justify-between px-4 py-3 bg-[#0f0f0f] cursor-pointer hover:bg-[#161616] transition-colors select-none"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-[#555] text-xs font-mono shrink-0">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="text-sm font-medium truncate">
            {dimension.name || <span className="text-[#555] italic">Untitled dimension</span>}
          </span>
          <span className="text-xs text-[#555] shrink-0">
            w: {dimension.weight.toFixed(2)}
          </span>
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-3">
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onMoveUp(); }}
            disabled={index === 0}
            className="px-2 py-1 text-[#555] hover:text-white disabled:opacity-25 disabled:cursor-not-allowed transition-colors text-xs"
            title="Move up"
          >
            ↑
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onMoveDown(); }}
            disabled={index === total - 1}
            className="px-2 py-1 text-[#555] hover:text-white disabled:opacity-25 disabled:cursor-not-allowed transition-colors text-xs"
            title="Move down"
          >
            ↓
          </button>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="px-2 py-1 text-[#555] hover:text-red-400 transition-colors text-xs"
            title="Delete dimension"
          >
            Remove
          </button>
          <span className="text-[#444] text-xs ml-1">
            {expanded ? "▲" : "▼"}
          </span>
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="p-4 flex flex-col gap-4 bg-[#0a0a0a]">
          {/* Name + Weight row */}
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-xs text-[#666] mb-1">Name</label>
              <input
                type="text"
                value={dimension.name}
                onChange={(e) => updateField("name", e.target.value)}
                className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
                placeholder="e.g. factual_accuracy"
              />
            </div>
            <div className="w-28">
              <label className="block text-xs text-[#666] mb-1">Weight (0–1)</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={dimension.weight}
                onChange={(e) => updateField("weight", parseFloat(e.target.value) || 0)}
                className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs text-[#666] mb-1">Description</label>
            <textarea
              value={dimension.description}
              onChange={(e) => updateField("description", e.target.value)}
              rows={2}
              className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555] resize-none"
              placeholder="What does this dimension measure?"
            />
          </div>

          {/* Levels */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-[#666]">Score levels</label>
              <span className="text-xs text-[#444]">1 = worst, 5 = best</span>
            </div>
            <p className="text-xs text-[#555] mb-3">
              Hint: A good level description is specific and observable, e.g., &quot;Includes numbered steps the user can follow&quot;
            </p>
            <div className="flex flex-col gap-2">
              {dimension.levels.map((level, li) => (
                <div key={level.score} className="flex gap-3 items-start">
                  <span className="text-xs text-[#555] font-mono w-5 pt-2.5 shrink-0">
                    {level.score}
                  </span>
                  <textarea
                    value={level.description}
                    onChange={(e) => updateLevel(li, e.target.value)}
                    rows={2}
                    className="flex-1 bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555] resize-none"
                    placeholder={`Score ${level.score} description`}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
