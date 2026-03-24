"use client";

import { use, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { getRunResults } from "@/lib/api";
import type { RunResultsData, RunCase, EvalCase, MergedCase } from "@/lib/types";
import CaseFilters from "@/components/responses/case-filters";
import CaseNav from "@/components/responses/case-nav";
import CaseViewer from "@/components/responses/case-viewer";

export default function ResponsesPage({
  params,
}: {
  params: Promise<{ id: string; runId: string }>;
}) {
  const { id, runId } = use(params);

  const [results, setResults] = useState<RunResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [winnerFilter, setWinnerFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("default");

  const handleCategoryChange = useCallback((v: string) => {
    setCategoryFilter(v);
    setCurrentIndex(0);
  }, []);

  const handleWinnerChange = useCallback((v: string) => {
    setWinnerFilter(v);
    setCurrentIndex(0);
  }, []);

  const handleSortChange = useCallback((v: string) => {
    setSortBy(v);
    setCurrentIndex(0);
  }, []);

  useEffect(() => {
    getRunResults(runId)
      .then(setResults)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [runId]);

  // Merge run_data and eval_data
  const merged: MergedCase[] = (() => {
    if (!results?.run_data || !results?.eval_data) return [];
    const runCases = (results.run_data as { results?: RunCase[] }).results ?? [];
    const evalCases = (results.eval_data as { evaluations?: EvalCase[] }).evaluations ?? [];

    const evalMap = new Map<string, EvalCase>();
    for (const ec of evalCases) {
      evalMap.set(ec.test_case_id, ec);
    }

    return runCases.map((rc) => {
      const ec = evalMap.get(rc.test_case_id);
      return {
        ...rc,
        pointwise: ec?.pointwise,
        pairwise: ec?.pairwise,
        skipped: ec?.skipped,
      };
    });
  })();

  // Extract prompt info from eval_data config
  const evalConfig = results?.eval_data
    ? (results.eval_data as { config?: { prompt_a?: { name?: string; key?: string }; prompt_b?: { name?: string; key?: string } } }).config
    : null;

  const promptAName = evalConfig?.prompt_a?.name ?? "Prompt A";
  const promptBName = evalConfig?.prompt_b?.name ?? "Prompt B";

  // Determine actual prompt keys from the first case responses
  const firstCase = merged[0];
  const responseKeys = firstCase ? Object.keys(firstCase.responses) : [];
  const promptAKey =
    evalConfig?.prompt_a?.key ??
    (responseKeys.includes("prompt_a") ? "prompt_a" : responseKeys[0] ?? "prompt_a");
  const promptBKey =
    evalConfig?.prompt_b?.key ??
    (responseKeys.includes("prompt_b") ? "prompt_b" : responseKeys[1] ?? "prompt_b");

  // Unique categories
  const categories = Array.from(new Set(merged.map((c) => c.category).filter(Boolean)));

  // Compute average pointwise score for a case and prompt key
  function avgScore(c: MergedCase, key: string): number {
    const dims = c.pointwise?.[key];
    if (!dims) return 0;
    const scores = Object.values(dims)
      .map((d) => d.score)
      .filter((s): s is number => s !== null);
    if (scores.length === 0) return 0;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  }

  function minScore(c: MergedCase): number {
    const allScores: number[] = [];
    if (c.pointwise) {
      for (const dims of Object.values(c.pointwise)) {
        for (const d of Object.values(dims)) {
          if (d.score !== null) allScores.push(d.score);
        }
      }
    }
    if (allScores.length === 0) return 5;
    return Math.min(...allScores);
  }

  // Filter
  const filtered = merged.filter((c) => {
    if (categoryFilter !== "all" && c.category !== categoryFilter) return false;
    if (winnerFilter !== "all") {
      const winner = c.pairwise?.winner;
      if (winnerFilter === "tie" && winner !== "tie") return false;
      if (winnerFilter === "prompt_a" && winner !== "prompt_a" && winner !== "a") return false;
      if (winnerFilter === "prompt_b" && winner !== "prompt_b" && winner !== "b") return false;
    }
    return true;
  });

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "biggest_delta") {
      const deltaA = Math.abs(avgScore(a, promptAKey) - avgScore(a, promptBKey));
      const deltaB = Math.abs(avgScore(b, promptAKey) - avgScore(b, promptBKey));
      return deltaB - deltaA;
    }
    if (sortBy === "lowest_score") {
      return minScore(a) - minScore(b);
    }
    return 0;
  });

  const clampedIndex = Math.min(currentIndex, Math.max(0, sorted.length - 1));
  const currentCase = sorted[clampedIndex] ?? null;

  const handlePrev = useCallback(() => {
    setCurrentIndex((i) => Math.max(0, i - 1));
  }, []);

  const handleNext = useCallback(() => {
    setCurrentIndex((i) => Math.min(sorted.length - 1, i + 1));
  }, [sorted.length]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handlePrev, handleNext]);

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">Failed to load: {error}</p>
      </div>
    );
  }

  if (merged.length === 0) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">No response data available for this run.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222] flex items-center justify-between">
        <h1 className="text-xl font-semibold">Browse Responses</h1>
        <Link
          href={`/experiments/${id}/results/${runId}`}
          className="text-[#888] text-sm hover:text-[#ededed]"
        >
          Back to results
        </Link>
      </div>

      <div className="p-8 space-y-5 max-w-5xl">
        <CaseFilters
          categories={categories}
          categoryFilter={categoryFilter}
          onCategoryChange={handleCategoryChange}
          winnerFilter={winnerFilter}
          onWinnerChange={handleWinnerChange}
          sortBy={sortBy}
          onSortChange={handleSortChange}
          totalCount={merged.length}
          filteredCount={sorted.length}
        />

        {sorted.length === 0 ? (
          <p className="text-[#555] text-sm">No cases match the current filters.</p>
        ) : (
          <>
            <CaseNav
              currentIndex={clampedIndex}
              totalCount={sorted.length}
              onPrev={handlePrev}
              onNext={handleNext}
            />
            {currentCase && (
              <CaseViewer
                case={currentCase}
                promptAKey={promptAKey}
                promptBKey={promptBKey}
                promptAName={promptAName}
                promptBName={promptBName}
              />
            )}
            <CaseNav
              currentIndex={clampedIndex}
              totalCount={sorted.length}
              onPrev={handlePrev}
              onNext={handleNext}
            />
          </>
        )}
      </div>
    </div>
  );
}
