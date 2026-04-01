"use client";

import { useState } from "react";
import type { ContextSourceConfig } from "@/lib/types";

interface ContextSourceEditorProps {
  value: ContextSourceConfig | undefined;
  onChange: (val: ContextSourceConfig | undefined) => void;
}

type ModeType = "none" | "script" | "http";

function getMode(value: ContextSourceConfig | undefined): ModeType {
  if (!value) return "none";
  return value.type;
}

export default function ContextSourceEditor({ value, onChange }: ContextSourceEditorProps) {
  const mode = getMode(value);

  const [testResult, setTestResult] = useState<{ success: boolean; context?: string; error?: string } | null>(null);
  const [testing, setTesting] = useState(false);

  // Headers state: stored as array of [key, value] pairs for editing
  const [headerRows, setHeaderRows] = useState<Array<{ key: string; value: string }>>(
    value?.headers
      ? Object.entries(value.headers).map(([k, v]) => ({ key: k, value: v }))
      : []
  );

  // Body template: stored as raw JSON string for textarea
  const [bodyJson, setBodyJson] = useState<string>(
    value?.body_template ? JSON.stringify(value.body_template, null, 2) : ""
  );
  const [bodyJsonError, setBodyJsonError] = useState<string | null>(null);

  function selectMode(newMode: ModeType) {
    setTestResult(null);
    if (newMode === "none") {
      onChange(undefined);
    } else if (newMode === "script") {
      onChange({ type: "script", command: "", timeout: 30 });
    } else {
      onChange({ type: "http", url: "", method: "POST", timeout: 30 });
    }
  }

  function updateScript(key: keyof ContextSourceConfig, val: unknown) {
    if (!value) return;
    onChange({ ...value, [key]: val } as ContextSourceConfig);
  }

  function updateHttp(key: keyof ContextSourceConfig, val: unknown) {
    if (!value) return;
    onChange({ ...value, [key]: val } as ContextSourceConfig);
  }

  function updateHeaderRow(index: number, field: "key" | "value", val: string) {
    if (!value) return;
    const updated = headerRows.map((row, i) => i === index ? { ...row, [field]: val } : row);
    setHeaderRows(updated);
    const headers: Record<string, string> = {};
    for (const row of updated) {
      if (row.key.trim()) headers[row.key.trim()] = row.value;
    }
    onChange({ ...value, headers } as ContextSourceConfig);
  }

  function addHeaderRow() {
    setHeaderRows((prev) => [...prev, { key: "", value: "" }]);
  }

  function removeHeaderRow(index: number) {
    if (!value) return;
    const updated = headerRows.filter((_, i) => i !== index);
    setHeaderRows(updated);
    const headers: Record<string, string> = {};
    for (const row of updated) {
      if (row.key.trim()) headers[row.key.trim()] = row.value;
    }
    onChange({ ...value, headers } as ContextSourceConfig);
  }

  function handleBodyJsonChange(raw: string) {
    setBodyJson(raw);
    setBodyJsonError(null);
    if (!value) return;
    if (!raw.trim()) {
      const { body_template: _removed, ...rest } = value;
      onChange(rest as ContextSourceConfig);
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      onChange({ ...value, body_template: parsed } as ContextSourceConfig);
    } catch {
      setBodyJsonError("Invalid JSON");
    }
  }

  async function handleTest() {
    if (!value) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch("/api/context-source/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config: value, input_text: "Hello, how are you?" }),
      });
      const data = await res.json();
      setTestResult(data);
    } catch (e) {
      setTestResult({ success: false, error: e instanceof Error ? e.message : "Request failed" });
    } finally {
      setTesting(false);
    }
  }

  const modeButtonBase =
    "flex-1 px-4 py-3 text-sm border rounded text-left transition-colors cursor-pointer";
  const modeButtonActive =
    "border-[#555] bg-[#111] text-[#ededed]";
  const modeButtonInactive =
    "border-[#222] bg-[#0a0a0a] text-[#888] hover:border-[#333] hover:text-[#aaa]";

  const inputClass =
    "w-full bg-[#111] border border-[#222] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]";
  const labelClass = "block text-xs text-[#666] mb-1";
  const helperClass = "text-xs text-[#555] mt-1";

  return (
    <div className="border border-[#222] rounded p-5 flex flex-col gap-4">
      <div>
        <p className="text-xs font-semibold text-[#888] uppercase tracking-wider mb-1">
          Context Source
        </p>
        <p className="text-xs text-[#555]">
          Automatically fetch context from an external source for test cases without static context
        </p>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2">
        {(["none", "script", "http"] as ModeType[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => selectMode(m)}
            className={`${modeButtonBase} ${mode === m ? modeButtonActive : modeButtonInactive}`}
          >
            <span className="font-medium capitalize">{m === "none" ? "None" : m === "script" ? "Script" : "HTTP"}</span>
            <span className="block text-xs text-[#555] mt-0.5">
              {m === "none" && "No dynamic context"}
              {m === "script" && "Run a shell command"}
              {m === "http" && "Call an HTTP endpoint"}
            </span>
          </button>
        ))}
      </div>

      {/* Script mode fields */}
      {mode === "script" && value && (
        <div className="flex flex-col gap-3">
          <div>
            <label className={labelClass}>Command</label>
            <input
              type="text"
              value={value.command ?? ""}
              onChange={(e) => updateScript("command", e.target.value)}
              className={inputClass}
              placeholder={`python my_rag.py --query '{input}'`}
            />
            <p className={helperClass}>Use {"{input}"} as placeholder for the test case input</p>
          </div>
          <div className="max-w-[160px]">
            <label className={labelClass}>Timeout (seconds)</label>
            <input
              type="number"
              min={1}
              value={value.timeout ?? 30}
              onChange={(e) => updateScript("timeout", parseInt(e.target.value, 10) || 30)}
              className={inputClass}
            />
          </div>
        </div>
      )}

      {/* HTTP mode fields */}
      {mode === "http" && value && (
        <div className="flex flex-col gap-3">
          <div>
            <label className={labelClass}>URL</label>
            <input
              type="text"
              value={value.url ?? ""}
              onChange={(e) => updateHttp("url", e.target.value)}
              className={inputClass}
              placeholder="https://my-rag-api.example.com/retrieve"
            />
          </div>

          <div className="max-w-[160px]">
            <label className={labelClass}>Method</label>
            <select
              value={value.method ?? "POST"}
              onChange={(e) => updateHttp("method", e.target.value as "GET" | "POST")}
              className={inputClass}
            >
              <option value="POST">POST</option>
              <option value="GET">GET</option>
            </select>
          </div>

          {/* Headers */}
          <div>
            <label className={labelClass}>Headers</label>
            <div className="flex flex-col gap-1.5">
              {headerRows.map((row, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <input
                    type="text"
                    value={row.key}
                    onChange={(e) => updateHeaderRow(i, "key", e.target.value)}
                    className="flex-1 bg-[#111] border border-[#222] rounded px-2 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
                    placeholder="Header name"
                  />
                  <input
                    type="text"
                    value={row.value}
                    onChange={(e) => updateHeaderRow(i, "value", e.target.value)}
                    className="flex-1 bg-[#111] border border-[#222] rounded px-2 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
                    placeholder="Value"
                  />
                  <button
                    type="button"
                    onClick={() => removeHeaderRow(i)}
                    className="text-[#555] hover:text-[#888] text-sm px-1"
                  >
                    x
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={addHeaderRow}
                className="text-xs text-[#555] hover:text-[#888] text-left mt-0.5"
              >
                + Add header
              </button>
            </div>
          </div>

          {/* Body template */}
          <div>
            <label className={labelClass}>Body template (JSON)</label>
            <textarea
              value={bodyJson}
              onChange={(e) => handleBodyJsonChange(e.target.value)}
              rows={4}
              className={`${inputClass} font-mono resize-none`}
              placeholder={`{"query": "{input}", "top_k": 5}`}
            />
            {bodyJsonError && (
              <p className="text-xs text-red-400 mt-1">{bodyJsonError}</p>
            )}
          </div>

          {/* Response path */}
          <div>
            <label className={labelClass}>Response path</label>
            <input
              type="text"
              value={value.response_path ?? ""}
              onChange={(e) => updateHttp("response_path", e.target.value || undefined)}
              className={inputClass}
              placeholder="data.context"
            />
            <p className={helperClass}>Dot-path to extract context from JSON response</p>
          </div>

          {/* Timeout */}
          <div className="max-w-[160px]">
            <label className={labelClass}>Timeout (seconds)</label>
            <input
              type="number"
              min={1}
              value={value.timeout ?? 30}
              onChange={(e) => updateHttp("timeout", parseInt(e.target.value, 10) || 30)}
              className={inputClass}
            />
          </div>
        </div>
      )}

      {/* Test button */}
      {mode !== "none" && (
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="self-start px-3 py-1.5 border border-[#333] text-sm rounded text-[#888] hover:text-white hover:border-[#555] transition-colors disabled:opacity-50"
          >
            {testing ? "Testing..." : "Test with sample input"}
          </button>
          {testResult && (
            <div
              className={`rounded p-3 text-sm border ${
                testResult.success
                  ? "border-[#333] bg-[#0f1a0f] text-[#ededed]"
                  : "border-red-900 bg-[#1a0f0f] text-red-400"
              }`}
            >
              {testResult.success ? (
                <pre className="whitespace-pre-wrap break-words text-xs text-[#aaa]">
                  {testResult.context}
                </pre>
              ) : (
                <p>{testResult.error}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
