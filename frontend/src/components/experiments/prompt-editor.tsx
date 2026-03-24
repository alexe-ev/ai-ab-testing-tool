"use client";

import { useRef, useEffect } from "react";
import ModelSelector from "./model-selector";
import { DEFAULT_PROMPT } from "./experiment-form";
import type { PromptConfig } from "@/lib/types";

interface PromptEditorProps {
  label: string;
  value: PromptConfig;
  onChange: (value: PromptConfig) => void;
}

export default function PromptEditor({ label, value, onChange }: PromptEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${ta.scrollHeight}px`;
  }, [value.system]);

  function update<K extends keyof PromptConfig>(key: K, val: PromptConfig[K]) {
    onChange({ ...value, [key]: val });
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs font-semibold text-[#888] uppercase tracking-wider">{label}</p>

      <div>
        <label className="block text-xs text-[#666] mb-1">Prompt name</label>
        <input
          type="text"
          value={value.name}
          onChange={(e) => update("name", e.target.value)}
          className="w-full bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
          placeholder="e.g. Minimal"
        />
      </div>

      <div>
        <label className="block text-xs text-[#666] mb-1">Model</label>
        <ModelSelector value={value.model} onChange={(v) => update("model", v)} />
      </div>

      <div>
        <label className="block text-xs text-[#666] mb-1">
          Temperature: {value.temperature.toFixed(1)}
        </label>
        <input
          type="range"
          min={0}
          max={2}
          step={0.1}
          value={value.temperature}
          onChange={(e) => update("temperature", parseFloat(e.target.value))}
          className="w-full accent-white"
        />
      </div>

      <div>
        <label className="block text-xs text-[#666] mb-1">Max tokens</label>
        <input
          type="number"
          min={1}
          max={32000}
          value={value.max_tokens}
          onChange={(e) => update("max_tokens", parseInt(e.target.value, 10) || DEFAULT_PROMPT.max_tokens)}
          className="w-full bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
        />
      </div>

      <div>
        <label className="block text-xs text-[#666] mb-1">System prompt</label>
        <textarea
          ref={textareaRef}
          value={value.system}
          onChange={(e) => update("system", e.target.value)}
          rows={6}
          className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] font-mono resize-none overflow-hidden focus:outline-none focus:border-[#555]"
          placeholder="You are a helpful assistant."
          style={{ fontFamily: "var(--font-geist-mono)" }}
        />
        <p className="text-xs text-[#555] mt-1 text-right">
          {value.system.length} chars
        </p>
      </div>
    </div>
  );
}
