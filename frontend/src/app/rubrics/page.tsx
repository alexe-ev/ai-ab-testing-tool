"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getRubrics, deleteRubric } from "@/lib/api";
import type { RubricListItem } from "@/lib/types";
import { EmptyState } from "@/components/ui/empty-state";

export default function RubricsPage() {
  const [rubrics, setRubrics] = useState<RubricListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRubrics()
      .then(setRubrics)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`Delete rubric "${name}"?`)) return;
    try {
      await deleteRubric(id);
      setRubrics((prev) => prev.filter((r) => r.id !== id));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Delete failed.");
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold">Rubrics</h1>
        <Link
          href="/rubrics/new"
          className="px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors"
        >
          New Rubric
        </Link>
      </div>

      {loading && (
        <p className="text-[#888] text-sm">Loading...</p>
      )}

      {error && (
        <p className="text-red-400 text-sm">Failed to load: {error}</p>
      )}

      {!loading && !error && rubrics.length === 0 && (
        <EmptyState
          title="No rubrics yet"
          description="Rubrics define how responses are scored. Each dimension (e.g. accuracy, tone) gets a weight and a 5-level scoring scale. Start from a template or build your own."
          actionLabel="New Rubric"
          actionHref="/rubrics/new"
        />
      )}

      {!loading && !error && rubrics.length > 0 && (
        <div className="flex flex-col gap-2">
          {rubrics.map((r) => (
            <div
              key={r.id}
              className="border border-[#222] rounded-lg p-4 hover:border-[#444] transition-colors flex items-center justify-between"
            >
              <Link href={`/rubrics/${r.id}/edit`} className="flex-1 min-w-0">
                <p className="font-medium text-sm">{r.name}</p>
              </Link>
              <button
                type="button"
                onClick={() => handleDelete(r.id, r.name)}
                className="ml-4 text-xs text-[#555] hover:text-red-400 transition-colors shrink-0"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
