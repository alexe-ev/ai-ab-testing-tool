"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import TestCaseTable, { makeEmptyCase } from "./test-case-table";
import type { EditableCase } from "./test-case-table";
import type { TestSetFormData, TestSet } from "@/lib/types";

// Lazy import to keep modal code-split
import dynamic from "next/dynamic";
const ImportModal = dynamic(() => import("./import-modal"), { ssr: false });

function casesToFormData(name: string, cases: EditableCase[]): TestSetFormData {
  return {
    name,
    cases: cases.map(({ case_identifier, category, input, context, reference }) => ({
      case_identifier,
      category,
      input,
      context: context || undefined,
      reference: reference || undefined,
    })),
  };
}

interface TestSetFormProps {
  initial?: {
    name: string;
    cases: EditableCase[];
  };
  onSave: (data: TestSetFormData) => Promise<TestSet | void>;
}

export default function TestSetForm({ initial, onSave }: TestSetFormProps) {
  const router = useRouter();
  const [name, setName] = useState(initial?.name ?? "");
  const [cases, setCases] = useState<EditableCase[]>(initial?.cases ?? [makeEmptyCase(0)]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);

  function handleImport(imported: EditableCase[]) {
    setCases((prev) => [...prev, ...imported]);
  }

  async function handleSave() {
    if (!name.trim()) {
      setError("Test set name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(casesToFormData(name, cases));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl">
      {/* Name */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider mb-4">
          Test Set
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
            placeholder="e.g. Support tickets v1"
          />
        </div>
      </section>

      {/* Cases */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs font-semibold text-[#888] uppercase tracking-wider">
            Test Cases ({cases.length})
          </h2>
          <button
            type="button"
            onClick={() => setShowImport(true)}
            className="text-xs px-3 py-1.5 border border-[#333] rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
          >
            Import
          </button>
        </div>
        <TestCaseTable cases={cases} onChange={setCases} />
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
          {saving ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/test-sets")}
          className="px-4 py-2 border border-[#333] text-sm rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
        >
          Cancel
        </button>
      </div>

      {showImport && (
        <ImportModal
          onImport={handleImport}
          onClose={() => setShowImport(false)}
        />
      )}
    </div>
  );
}
