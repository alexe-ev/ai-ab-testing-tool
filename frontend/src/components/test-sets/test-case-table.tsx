"use client";

import { useState } from "react";
import Tooltip from "@/components/ui/tooltip";

export interface EditableCase {
  _key: string; // local-only stable key for React
  case_identifier: string;
  category: string;
  input: string;
  context: string;
  reference: string;
}

interface TestCaseTableProps {
  cases: EditableCase[];
  onChange: (cases: EditableCase[]) => void;
}

export function makeEmptyCase(index: number): EditableCase {
  return {
    _key: `case-${Date.now()}-${index}`,
    case_identifier: `case-${index + 1}`,
    category: "",
    input: "",
    context: "",
    reference: "",
  };
}

export default function TestCaseTable({ cases, onChange }: TestCaseTableProps) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("");

  const categories = Array.from(new Set(cases.map((c) => c.category).filter(Boolean)));

  const categoryCounts = categories.reduce<Record<string, number>>((acc, cat) => {
    acc[cat] = cases.filter((c) => c.category === cat).length;
    return acc;
  }, {});

  const filtered = categoryFilter
    ? cases.filter((c) => c.category === categoryFilter)
    : cases;

  function updateCase(key: string, updates: Partial<EditableCase>) {
    onChange(cases.map((c) => (c._key === key ? { ...c, ...updates } : c)));
  }

  function deleteCase(key: string) {
    onChange(cases.filter((c) => c._key !== key));
    if (expandedKey === key) setExpandedKey(null);
  }

  function duplicateCase(key: string) {
    const idx = cases.findIndex((c) => c._key === key);
    if (idx === -1) return;
    const original = cases[idx];
    const copy: EditableCase = {
      ...original,
      _key: `case-${Date.now()}-dup`,
      case_identifier: `${original.case_identifier}-copy`,
    };
    const next = [...cases];
    next.splice(idx + 1, 0, copy);
    onChange(next);
  }

  function addCase() {
    const newCase = makeEmptyCase(cases.length);
    const updated = [...cases, newCase];
    onChange(updated);
    setExpandedKey(newCase._key);
  }

  return (
    <div>
      {/* Header row: category filter + counts + add button */}
      <div className="flex items-center justify-between mb-3 gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-[#ededed] focus:outline-none focus:border-[#555]"
          >
            <option value="">All categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat} ({categoryCounts[cat]})
              </option>
            ))}
          </select>
          {categories.length > 0 && (
            <span className="text-xs text-[#555]">
              {categories.map((cat) => `${cat}: ${categoryCounts[cat]}`).join(" · ")}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={addCase}
          className="px-3 py-1.5 text-xs border border-[#333] rounded text-[#888] hover:text-white hover:border-[#555] transition-colors shrink-0"
        >
          + Add Case
        </button>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="border border-[#222] rounded-lg p-8 text-center">
          <p className="text-[#555] text-sm">No cases yet. Click &quot;+ Add Case&quot; to start.</p>
        </div>
      ) : (
        <div className="border border-[#222] rounded-lg overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-[2rem_8rem_1fr_2rem_7rem] gap-0 px-4 py-2 border-b border-[#222] bg-[#0d0d0d]">
            <span className="text-xs text-[#555] font-medium">#</span>
            <span className="text-xs text-[#555] font-medium">Category</span>
            <span className="text-xs text-[#555] font-medium">Input</span>
            <Tooltip text="Optional background info sent with the user input, e.g. account details or retrieved documents.">
              <span className="text-xs text-[#555] font-medium">Context</span>
            </Tooltip>
            <span className="text-xs text-[#555] font-medium">Actions</span>
          </div>

          {filtered.map((c, i) => {
            const globalIdx = cases.findIndex((x) => x._key === c._key);
            const expanded = expandedKey === c._key;

            return (
              <div key={c._key} className="border-b border-[#1a1a1a] last:border-b-0">
                {/* Row */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => setExpandedKey(expanded ? null : c._key)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setExpandedKey(expanded ? null : c._key); } }}
                  className="w-full grid grid-cols-[2rem_8rem_1fr_2rem_7rem] gap-0 px-4 py-3 text-left hover:bg-[#0d0d0d] transition-colors cursor-pointer"
                >
                  <span className="text-xs text-[#555]">{i + 1}</span>
                  <span className="text-xs text-[#888] truncate pr-2">
                    {c.category || <span className="text-[#444]">—</span>}
                  </span>
                  <span className="text-xs text-[#ededed] truncate pr-2">
                    {c.input || <span className="text-[#444]">empty</span>}
                  </span>
                  <span className="text-xs text-[#555]">
                    {c.context ? "●" : ""}
                  </span>
                  <span
                    className="flex items-center gap-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      onClick={() => duplicateCase(c._key)}
                      className="text-xs text-[#555] hover:text-[#aaa] transition-colors"
                      title="Duplicate"
                    >
                      Dup
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteCase(c._key)}
                      className="text-xs text-[#555] hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      Del
                    </button>
                  </span>
                </div>

                {/* Inline editor */}
                {expanded && (
                  <div className="px-4 pb-4 bg-[#0a0a0a] border-t border-[#1a1a1a] flex flex-col gap-3">
                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <div>
                        <label className="block text-xs text-[#666] mb-1">ID</label>
                        <input
                          type="text"
                          value={c.case_identifier}
                          onChange={(e) =>
                            updateCase(c._key, { case_identifier: e.target.value })
                          }
                          className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[#666] mb-1">Category</label>
                        <input
                          type="text"
                          value={c.category}
                          onChange={(e) =>
                            updateCase(c._key, { category: e.target.value })
                          }
                          className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
                          placeholder="e.g. billing"
                          list={`cat-suggestions-${globalIdx}`}
                        />
                        <datalist id={`cat-suggestions-${globalIdx}`}>
                          {categories.map((cat) => (
                            <option key={cat} value={cat} />
                          ))}
                        </datalist>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-[#666] mb-1">Input</label>
                      <textarea
                        value={c.input}
                        onChange={(e) => updateCase(c._key, { input: e.target.value })}
                        rows={3}
                        className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] resize-none focus:outline-none focus:border-[#555]"
                        placeholder="The user message or input to test"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-[#666] mb-1">Context (optional)</label>
                      <textarea
                        value={c.context}
                        onChange={(e) => updateCase(c._key, { context: e.target.value })}
                        rows={2}
                        className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] resize-none focus:outline-none focus:border-[#555]"
                        placeholder="Additional context passed to the model"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-[#666] mb-1">Reference (optional)</label>
                      <textarea
                        value={c.reference}
                        onChange={(e) => updateCase(c._key, { reference: e.target.value })}
                        rows={2}
                        className="w-full bg-[#111] border border-[#333] rounded px-3 py-2 text-sm text-[#ededed] resize-none focus:outline-none focus:border-[#555]"
                        placeholder="Expected ideal answer (used by judge)"
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
