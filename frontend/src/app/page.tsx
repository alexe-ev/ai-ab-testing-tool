"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getExperiments } from "@/lib/api";
import type { ExperimentListItem, SummaryMetrics } from "@/lib/types";

function confidenceColor(confidence: string): string {
  if (confidence === "high") return "bg-green-900 text-green-300 border-green-700";
  if (confidence === "medium") return "bg-yellow-900 text-yellow-300 border-yellow-700";
  return "bg-[#1a1a1a] text-[#888] border-[#333]";
}

function MetricsBadge({ metrics }: { metrics: SummaryMetrics }) {
  return (
    <div className="flex items-center gap-2 mt-2">
      <span
        className={`text-xs px-2 py-0.5 rounded border ${confidenceColor(metrics.confidence)}`}
      >
        {metrics.winner}
      </span>
      <span className="text-xs text-[#666]">
        {metrics.score_a.toFixed(2)} / {metrics.score_b.toFixed(2)}
      </span>
      <span className="text-xs text-[#555]">
        Δ {metrics.score_delta.toFixed(2)}
      </span>
      <span className="text-xs text-[#555] capitalize">
        {metrics.confidence} confidence
      </span>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<ExperimentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getExperiments()
      .then(setExperiments)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold">Experiments</h1>
        <Link
          href="/experiments/new"
          className="px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors"
        >
          New Experiment
        </Link>
      </div>

      {loading && (
        <p className="text-[#888] text-sm">Loading...</p>
      )}

      {error && (
        <p className="text-red-400 text-sm">Failed to load: {error}</p>
      )}

      {!loading && !error && experiments.length === 0 && (
        <div className="border border-[#222] rounded-lg p-12 text-center">
          <p className="text-[#888] text-sm mb-4">No experiments yet.</p>
          <Link
            href="/experiments/new"
            className="text-sm text-white underline underline-offset-2"
          >
            Create your first experiment
          </Link>
        </div>
      )}

      {!loading && !error && experiments.length > 0 && (
        <div className="flex flex-col gap-2">
          {experiments.map((exp) => (
            <div
              key={exp.id}
              className="border border-[#222] rounded-lg p-4 hover:border-[#444] transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{exp.name}</p>
                  {exp.description && (
                    <p className="text-[#888] text-xs mt-1 line-clamp-2">
                      {exp.description}
                    </p>
                  )}
                  {exp.last_run_metrics ? (
                    <MetricsBadge metrics={exp.last_run_metrics} />
                  ) : (
                    <p className="text-xs text-[#555] mt-2">No results yet</p>
                  )}
                </div>
                <div className="flex items-center gap-3 ml-4 shrink-0">
                  <div className="text-right">
                    <span className="block text-[#555] text-xs">
                      {exp.run_count} {exp.run_count === 1 ? "run" : "runs"}
                    </span>
                    {exp.last_run_at && (
                      <span className="block text-[#444] text-xs mt-0.5">
                        {formatDate(exp.last_run_at)}
                      </span>
                    )}
                  </div>
                  <Link
                    href={`/experiments/${exp.id}/run`}
                    className="text-xs text-[#888] hover:text-[#ededed] border border-[#333] rounded px-2 py-1 transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Run
                  </Link>
                  <Link
                    href={`/experiments/${exp.id}/edit`}
                    className="text-xs text-[#888] hover:text-[#ededed]"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Edit
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
