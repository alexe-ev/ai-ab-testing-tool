"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTestSets, deleteTestSet } from "@/lib/api";
import type { TestSetListItem } from "@/lib/types";
import { EmptyState } from "@/components/ui/empty-state";

export default function TestSetsPage() {
  const [testSets, setTestSets] = useState<TestSetListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTestSets()
      .then(setTestSets)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string, name: string) {
    if (!window.confirm(`Delete test set "${name}"?`)) return;
    try {
      await deleteTestSet(id);
      setTestSets((prev) => prev.filter((ts) => ts.id !== id));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Delete failed.");
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold">Test Sets</h1>
        <Link
          href="/test-sets/new"
          className="px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors"
        >
          New Test Set
        </Link>
      </div>

      {loading && (
        <p className="text-[#888] text-sm">Loading...</p>
      )}

      {error && (
        <p className="text-red-400 text-sm">Failed to load: {error}</p>
      )}

      {!loading && !error && testSets.length === 0 && (
        <EmptyState
          title="No test sets yet"
          description="Test sets are the inputs your AI will respond to. Each test case is a user message that both prompt variants will answer."
          actionLabel="New Test Set"
          actionHref="/test-sets/new"
        />
      )}

      {!loading && !error && testSets.length > 0 && (
        <div className="flex flex-col gap-2">
          {testSets.map((ts) => (
            <div
              key={ts.id}
              className="border border-[#222] rounded-lg p-4 hover:border-[#444] transition-colors flex items-center justify-between"
            >
              <Link href={`/test-sets/${ts.id}/edit`} className="flex-1 min-w-0">
                <p className="font-medium text-sm">{ts.name}</p>
                <p className="text-[#888] text-xs mt-1">
                  {ts.case_count} {ts.case_count === 1 ? "case" : "cases"}
                </p>
              </Link>
              <button
                type="button"
                onClick={() => handleDelete(ts.id, ts.name)}
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
