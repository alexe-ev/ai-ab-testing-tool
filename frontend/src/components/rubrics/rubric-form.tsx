"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import DimensionEditor from "./dimension-editor";
import { RUBRIC_TEMPLATES, makeEmptyDimension } from "@/lib/rubric-templates";
import type { RubricFormData, RubricDimensionFormData } from "@/lib/types";

interface RubricFormProps {
  initial?: {
    name: string;
    dimensions: RubricDimensionFormData[];
  };
  onSave: (data: RubricFormData) => Promise<void>;
}

export default function RubricForm({ initial, onSave }: RubricFormProps) {
  const router = useRouter();
  const [name, setName] = useState(initial?.name ?? "");
  const [dimensions, setDimensions] = useState<RubricDimensionFormData[]>(
    initial?.dimensions ?? []
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isNew = !initial;
  const showTemplatePicker = isNew && dimensions.length === 0;

  const totalWeight = dimensions.reduce((sum, d) => sum + d.weight, 0);
  const weightOk = dimensions.length === 0 || Math.abs(totalWeight - 1.0) <= 0.01;

  function applyTemplate(templateIndex: number) {
    const tpl = RUBRIC_TEMPLATES[templateIndex];
    if (!name) setName(tpl.name);
    setDimensions(
      tpl.dimensions.map((d) => ({
        name: d.name,
        description: d.description,
        weight: d.weight,
        levels: d.levels.map((l) => ({ ...l })),
      }))
    );
  }

  function addDimension() {
    setDimensions((prev) => [...prev, makeEmptyDimension()]);
  }

  function updateDimension(index: number, updated: RubricDimensionFormData) {
    setDimensions((prev) => prev.map((d, i) => (i === index ? updated : d)));
  }

  function deleteDimension(index: number) {
    setDimensions((prev) => prev.filter((_, i) => i !== index));
  }

  function moveUp(index: number) {
    if (index === 0) return;
    setDimensions((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next;
    });
  }

  function moveDown(index: number) {
    if (index === dimensions.length - 1) return;
    setDimensions((prev) => {
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next;
    });
  }

  function autoNormalize() {
    if (dimensions.length === 0) return;
    const base = parseFloat((1.0 / dimensions.length).toFixed(4));
    setDimensions((prev) =>
      prev.map((d, i) => ({
        ...d,
        weight: i === prev.length - 1
          ? parseFloat((1.0 - base * (prev.length - 1)).toFixed(4))
          : base,
      }))
    );
  }

  async function handleSave() {
    if (!name.trim()) {
      setError("Rubric name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave({ name, dimensions });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8 max-w-3xl">
      {/* Name */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider mb-4">
          Rubric
        </h2>
        <div>
          <label className="block text-xs text-[#666] mb-1">
            Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full max-w-md bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
            placeholder="e.g. Customer Support v1"
          />
        </div>
      </section>

      {/* Template picker */}
      {showTemplatePicker && (
        <section className="mb-8">
          <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider mb-4">
            Start from template
          </h2>
          <div className="flex gap-3 flex-wrap">
            {RUBRIC_TEMPLATES.map((tpl, i) => (
              <button
                key={tpl.name}
                type="button"
                onClick={() => applyTemplate(i)}
                className="px-4 py-2 border border-[#333] rounded text-sm text-[#aaa] hover:text-white hover:border-[#555] transition-colors"
              >
                {tpl.name}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Dimensions */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider">
            Dimensions ({dimensions.length})
          </h2>
        </div>

        {dimensions.length === 0 && (
          <div className="border border-dashed border-[#333] rounded-lg p-8 text-center mb-4">
            <p className="text-[#555] text-sm">No dimensions yet.</p>
          </div>
        )}

        {dimensions.length > 0 && (
          <div className="flex flex-col gap-3 mb-4">
            {dimensions.map((dim, i) => (
              <DimensionEditor
                key={i}
                dimension={dim}
                index={i}
                total={dimensions.length}
                onChange={(updated) => updateDimension(i, updated)}
                onDelete={() => deleteDimension(i)}
                onMoveUp={() => moveUp(i)}
                onMoveDown={() => moveDown(i)}
              />
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={addDimension}
          className="text-sm px-3 py-1.5 border border-[#333] rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
        >
          + Add Dimension
        </button>
      </section>

      {/* Weight summary */}
      {dimensions.length > 0 && (
        <section className="mb-8 border border-[#222] rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs text-[#666]">Total weight:</span>
              <span
                className={`text-sm font-mono font-medium ${
                  weightOk ? "text-green-400" : "text-yellow-400"
                }`}
              >
                {totalWeight.toFixed(2)}
              </span>
              {!weightOk && (
                <span className="text-xs text-yellow-400">
                  Should sum to 1.00
                </span>
              )}
            </div>
            <button
              type="button"
              onClick={autoNormalize}
              className="text-xs px-3 py-1.5 border border-[#333] rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
            >
              Auto-normalize
            </button>
          </div>
        </section>
      )}

      {/* Actions */}
      {error && (
        <p className="text-red-400 text-sm mb-4">{error}</p>
      )}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/rubrics")}
          className="px-4 py-2 border border-[#333] text-sm rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
