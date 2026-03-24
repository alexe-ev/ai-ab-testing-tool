"use client";

import { useRef, useState } from "react";
import type { EditableCase } from "./test-case-table";

interface ImportModalProps {
  onImport: (cases: EditableCase[]) => void;
  onClose: () => void;
}

interface YamlCase {
  id?: string;
  case_identifier?: string;
  category?: string;
  input?: string;
  context?: string;
  reference?: string;
}

function parseYaml(text: string): EditableCase[] {
  // Dynamic import of js-yaml at call time
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const jsYaml = require("js-yaml") as { load: (s: string) => unknown };
  const doc = jsYaml.load(text) as { test_cases?: YamlCase[] } | YamlCase[] | null;

  let rawCases: YamlCase[] = [];
  if (doc && typeof doc === "object" && !Array.isArray(doc) && "test_cases" in doc && Array.isArray(doc.test_cases)) {
    rawCases = doc.test_cases;
  } else if (Array.isArray(doc)) {
    rawCases = doc as YamlCase[];
  }

  return rawCases.map((c, i) => ({
    _key: `import-${Date.now()}-${i}`,
    case_identifier: c.id ?? c.case_identifier ?? `case-${i + 1}`,
    category: c.category ?? "",
    input: c.input ?? "",
    context: c.context ?? "",
    reference: c.reference ?? "",
  }));
}

function parseCsv(text: string): EditableCase[] {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return [];

  const headers = lines[0].split(",").map((h) => h.trim().replace(/^["']|["']$/g, ""));

  return lines.slice(1).map((line, i) => {
    // Simple CSV split (handles quoted fields with no embedded newlines)
    const values: string[] = [];
    let current = "";
    let inQuote = false;
    for (let ci = 0; ci < line.length; ci++) {
      const ch = line[ci];
      if (ch === '"' && !inQuote) {
        inQuote = true;
      } else if (ch === '"' && inQuote) {
        inQuote = false;
      } else if (ch === "," && !inQuote) {
        values.push(current);
        current = "";
      } else {
        current += ch;
      }
    }
    values.push(current);

    const get = (key: string) =>
      (values[headers.indexOf(key)] ?? "").trim();

    return {
      _key: `import-${Date.now()}-${i}`,
      case_identifier: get("id") || get("case_identifier") || `case-${i + 1}`,
      category: get("category"),
      input: get("input"),
      context: get("context"),
      reference: get("reference"),
    };
  });
}

export default function ImportModal({ onImport, onClose }: ImportModalProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<EditableCase[] | null>(null);
  const [filename, setFilename] = useState<string>("");

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFilename(file.name);
    setError(null);
    setPreview(null);

    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      try {
        const ext = file.name.split(".").pop()?.toLowerCase();
        let parsed: EditableCase[] = [];
        if (ext === "yaml" || ext === "yml") {
          parsed = parseYaml(text);
        } else if (ext === "csv") {
          parsed = parseCsv(text);
        } else {
          setError("Unsupported file type. Use .yaml, .yml, or .csv.");
          return;
        }
        if (parsed.length === 0) {
          setError("No cases found in file.");
          return;
        }
        setPreview(parsed);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Parse error.");
      }
    };
    reader.readAsText(file);
  }

  function handleImport() {
    if (!preview) return;
    onImport(preview);
    onClose();
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-[#111] border border-[#333] rounded-lg w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold">Import Cases</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-[#555] hover:text-white text-lg leading-none"
          >
            ×
          </button>
        </div>

        <p className="text-xs text-[#666] mb-4">
          Accepts .yaml/.yml (with <code className="text-[#888]">test_cases</code> key) or .csv (header: id, category, input, context, reference).
          Parsed cases will be appended to the table.
        </p>

        <div
          className="border border-dashed border-[#333] rounded-lg p-6 text-center cursor-pointer hover:border-[#555] transition-colors mb-4"
          onClick={() => fileRef.current?.click()}
        >
          {filename ? (
            <p className="text-sm text-[#ededed]">{filename}</p>
          ) : (
            <p className="text-sm text-[#555]">Click to select file</p>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".yaml,.yml,.csv"
            onChange={handleFile}
            className="hidden"
          />
        </div>

        {error && (
          <p className="text-red-400 text-xs mb-4">{error}</p>
        )}

        {preview && (
          <div className="mb-4">
            <p className="text-xs text-[#888] mb-2">
              {preview.length} {preview.length === 1 ? "case" : "cases"} found
            </p>
            <div className="max-h-40 overflow-y-auto border border-[#222] rounded">
              {preview.slice(0, 10).map((c, i) => (
                <div key={i} className="px-3 py-2 border-b border-[#1a1a1a] last:border-b-0">
                  <span className="text-xs text-[#555] mr-2">{c.case_identifier}</span>
                  <span className="text-xs text-[#888] truncate">{c.input}</span>
                </div>
              ))}
              {preview.length > 10 && (
                <div className="px-3 py-2 text-xs text-[#555]">
                  +{preview.length - 10} more
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-[#333] text-sm rounded text-[#888] hover:text-white hover:border-[#555] transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleImport}
            disabled={!preview}
            className="px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] disabled:opacity-50 transition-colors"
          >
            Import {preview ? `${preview.length} cases` : ""}
          </button>
        </div>
      </div>
    </div>
  );
}
