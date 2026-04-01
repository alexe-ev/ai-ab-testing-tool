"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import PromptEditor from "./prompt-editor";
import DiffViewer from "./diff-viewer";
import ModelSelector from "./model-selector";
import ContextSourceEditor from "./context-source-editor";
import type { ExperimentFormData, PromptConfig, ContextSourceConfig } from "@/lib/types";

export const DEFAULT_PROMPT: PromptConfig = {
  name: "",
  system: "",
  model: "gpt-4o",
  temperature: 0.7,
  max_tokens: 512,
};

export const DEFAULT_FORM: ExperimentFormData = {
  name: "",
  description: "",
  hypothesis: "",
  config: {
    prompts: {
      a: { ...DEFAULT_PROMPT, name: "Prompt A" },
      b: { ...DEFAULT_PROMPT, name: "Prompt B" },
    },
    judge_model: "claude-sonnet",
  },
};

interface ExperimentFormProps {
  initial?: ExperimentFormData;
  onSave: (data: ExperimentFormData) => Promise<void>;
}

export default function ExperimentForm({ initial, onSave }: ExperimentFormProps) {
  const router = useRouter();
  const [form, setForm] = useState<ExperimentFormData>(initial ?? DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);

  function updateMeta(key: "name" | "description" | "hypothesis", val: string) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  function updatePrompt(which: "a" | "b", val: PromptConfig) {
    setForm((f) => ({
      ...f,
      config: {
        ...f.config,
        prompts: { ...f.config.prompts, [which]: val },
      },
    }));
  }

  function updateJudgeModel(val: string) {
    setForm((f) => ({
      ...f,
      config: { ...f.config, judge_model: val },
    }));
  }

  function updateContextSource(val: ContextSourceConfig | undefined) {
    setForm((f) => ({
      ...f,
      config: { ...f.config, context_source: val },
    }));
  }

  function updateContextTemplate(val: string | undefined) {
    setForm((f) => ({
      ...f,
      config: { ...f.config, context_template: val },
    }));
  }

  function updateContextPosition(val: "user" | "system") {
    setForm((f) => ({
      ...f,
      config: { ...f.config, context_position: val },
    }));
  }

  async function handleSave() {
    if (!form.name.trim()) {
      setError("Experiment name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(form);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl">
      {/* Metadata */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider mb-4">
          Experiment
        </h2>
        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-xs text-[#666] mb-1">
              Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => updateMeta("name", e.target.value)}
              className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
              placeholder="e.g. Support tone v2"
            />
          </div>
          <div>
            <label className="block text-xs text-[#666] mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => updateMeta("description", e.target.value)}
              rows={2}
              className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] resize-none focus:outline-none focus:border-[#555]"
              placeholder="What are you testing?"
            />
          </div>
          <div>
            <label className="block text-xs text-[#666] mb-1">Hypothesis</label>
            <textarea
              value={form.hypothesis}
              onChange={(e) => updateMeta("hypothesis", e.target.value)}
              rows={2}
              className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] resize-none focus:outline-none focus:border-[#555]"
              placeholder="e.g. Prompt B will score higher on accuracy dimension."
            />
          </div>
        </div>
      </section>

      {/* Prompt editors */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider">
            Prompts
          </h2>
          <button
            type="button"
            onClick={() => setShowDiff((v) => !v)}
            className="text-xs px-3 py-1.5 border border-[#333] rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
          >
            {showDiff ? "Show Editor" : "Show Diff"}
          </button>
        </div>

        {showDiff ? (
          <DiffViewer
            textA={form.config.prompts.a.system}
            textB={form.config.prompts.b.system}
            labelA={form.config.prompts.a.name || "Prompt A"}
            labelB={form.config.prompts.b.name || "Prompt B"}
          />
        ) : (
          <div className="grid grid-cols-2 gap-6">
            <PromptEditor
              label="Prompt A"
              value={form.config.prompts.a}
              onChange={(v) => updatePrompt("a", v)}
            />
            <PromptEditor
              label="Prompt B"
              value={form.config.prompts.b}
              onChange={(v) => updatePrompt("b", v)}
            />
          </div>
        )}
      </section>

      {/* Judge model */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider mb-4">
          Judge Model
        </h2>
        <div className="max-w-xs">
          <ModelSelector
            value={form.config.judge_model}
            onChange={updateJudgeModel}
          />
        </div>
      </section>

      {/* Context source */}
      <section className="mb-8">
        <ContextSourceEditor
          value={form.config.context_source}
          onChange={updateContextSource}
          contextTemplate={form.config.context_template}
          onContextTemplateChange={updateContextTemplate}
          contextPosition={form.config.context_position}
          onContextPositionChange={updateContextPosition}
        />
      </section>

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
          {saving ? "Saving..." : "Save Draft"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/")}
          className="px-4 py-2 border border-[#333] text-sm rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
