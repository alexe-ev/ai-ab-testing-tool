"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { getRunResults } from "@/lib/api";
import type { RunResultsData, AnalysisData } from "@/lib/types";

import SummaryCard from "@/components/results/summary-card";
import ScoreComparison from "@/components/results/score-comparison";
import DimensionTable from "@/components/results/dimension-table";
import PairwiseCard from "@/components/results/pairwise-card";
import CategoryBreakdown from "@/components/results/category-breakdown";
import NotableCases from "@/components/results/notable-cases";
import OperationalMetricsPanel from "@/components/results/operational-metrics";
import ExportButtons from "@/components/results/export-buttons";

export default function ResultsPage({
  params,
}: {
  params: Promise<{ id: string; runId: string }>;
}) {
  const { id, runId } = use(params);

  const [results, setResults] = useState<RunResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRunResults(runId)
      .then(setResults)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [runId]);

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading results...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">Failed to load results: {error}</p>
      </div>
    );
  }

  if (!results || !results.analysis) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">No analysis data available for this run.</p>
      </div>
    );
  }

  const analysis: AnalysisData = results.analysis.analysis;
  const promptA = analysis.prompt_a.name;
  const promptB = analysis.prompt_b.name;

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222] flex items-center justify-between">
        <h1 className="text-xl font-semibold">Results</h1>
        <Link
          href={`/experiments/${id}`}
          className="text-[#888] text-sm hover:text-[#ededed]"
        >
          Back to experiment
        </Link>
      </div>

      <div className="p-8 max-w-4xl space-y-5">
        <div>
          <Link
            href={`/experiments/${id}/results/${runId}/responses`}
            className="inline-block px-3 py-1.5 text-sm border border-[#333] rounded text-[#888] hover:text-[#ededed] hover:border-[#555]"
          >
            Browse Responses
          </Link>
        </div>

        <SummaryCard
          recommendation={analysis.recommendation}
          pairwise={analysis.pairwise}
          overall={analysis.pointwise.overall_weighted}
          promptA={promptA}
          promptB={promptB}
        />

        <ScoreComparison
          overall={analysis.pointwise.overall_weighted}
          promptA={promptA}
          promptB={promptB}
        />

        <DimensionTable
          dimensions={analysis.pointwise.dimensions}
          promptA={promptA}
          promptB={promptB}
        />

        {analysis.pairwise && (
          <PairwiseCard
            pairwise={analysis.pairwise}
            promptA={promptA}
            promptB={promptB}
          />
        )}

        {analysis.category_breakdown &&
          Object.keys(analysis.category_breakdown).length > 0 && (
            <CategoryBreakdown
              categories={analysis.category_breakdown}
              promptA={promptA}
              promptB={promptB}
              overallWinner={analysis.recommendation.winner}
            />
          )}

        {analysis.notable_cases &&
          Object.keys(analysis.notable_cases).length > 0 && (
            <NotableCases
              cases={analysis.notable_cases}
              promptA={promptA}
              promptB={promptB}
            />
          )}

        {analysis.operational_metrics && (
          <OperationalMetricsPanel
            metrics={analysis.operational_metrics}
            promptA={promptA}
            promptB={promptB}
          />
        )}

        <ExportButtons runId={runId} />
      </div>
    </div>
  );
}
