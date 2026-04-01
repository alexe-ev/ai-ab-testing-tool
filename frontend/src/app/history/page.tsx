"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getRunHistory, getExperiments } from "@/lib/api";
import type { RunHistoryItem, ExperimentListItem } from "@/lib/types";
import Link from "next/link";
import { EmptyState } from "@/components/ui/empty-state";

const STATUS_OPTIONS = ["", "complete", "failed", "running", "pending"];
const SORT_COLUMNS = [
  { key: "created_at", label: "Date" },
  { key: "score_delta", label: "Delta" },
];
const LIMIT = 20;

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function statusBadge(status: string): string {
  if (status === "complete") return "text-green-400";
  if (status === "failed") return "text-red-400";
  if (status === "running") return "text-yellow-400";
  return "text-[#888]";
}

function confidenceBadge(confidence: string): string {
  if (confidence === "high") return "text-green-400";
  if (confidence === "medium") return "text-yellow-400";
  return "text-[#666]";
}

export default function HistoryPage() {
  const router = useRouter();
  const [items, setItems] = useState<RunHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [experiments, setExperiments] = useState<ExperimentListItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const [filterExperiment, setFilterExperiment] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterModel, setFilterModel] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    getExperiments()
      .then(setExperiments)
      .catch((e: unknown) => console.error("Failed to load experiments:", e));
  }, []);

  const fetchRuns = useCallback(() => {
    setLoading(true);
    setError(null);
    getRunHistory({
      experiment_id: filterExperiment || undefined,
      status: filterStatus || undefined,
      model: filterModel || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      limit: LIMIT,
      offset,
    })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [filterExperiment, filterStatus, filterModel, sortBy, sortOrder, offset]);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  function handleSortClick(col: string) {
    if (sortBy === col) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
    setOffset(0);
  }

  const totalPages = Math.ceil(total / LIMIT);
  const currentPage = Math.floor(offset / LIMIT) + 1;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-xl font-semibold">Run History</h1>
        <span className="text-[#555] text-sm">{total} total</span>
      </div>

      {/* Filter bar */}
      <div className="flex gap-3 mb-6 flex-wrap items-center">
        <select
          value={filterExperiment}
          onChange={(e) => { setFilterExperiment(e.target.value); setOffset(0); }}
          className="bg-[#111] border border-[#333] text-[#ededed] text-sm rounded px-3 py-1.5 focus:outline-none focus:border-[#555]"
        >
          <option value="">All experiments</option>
          {experiments.map((exp) => (
            <option key={exp.id} value={exp.id}>{exp.name}</option>
          ))}
        </select>

        <select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); setOffset(0); }}
          className="bg-[#111] border border-[#333] text-[#ededed] text-sm rounded px-3 py-1.5 focus:outline-none focus:border-[#555]"
        >
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s || "All statuses"}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Filter by model..."
          value={filterModel}
          onChange={(e) => { setFilterModel(e.target.value); setOffset(0); }}
          className="bg-[#111] border border-[#333] text-[#ededed] text-sm rounded px-3 py-1.5 focus:outline-none focus:border-[#555] w-44"
        />

        {selectedIds.length > 0 && (
          <span className="text-[#555] text-xs">{selectedIds.length} selected</span>
        )}

        {selectedIds.length === 2 ? (
          <Link
            href={`/history/compare?a=${encodeURIComponent(selectedIds[0])}&b=${encodeURIComponent(selectedIds[1])}`}
            className="px-3 py-1.5 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors"
          >
            Compare
          </Link>
        ) : (
          <button
            disabled
            className="px-3 py-1.5 border border-[#333] text-sm rounded text-[#555] opacity-40 cursor-not-allowed"
          >
            Compare
          </button>
        )}
      </div>

      {loading && (
        <p className="text-[#888] text-sm">Loading...</p>
      )}

      {error && (
        <p className="text-red-400 text-sm mb-4">Failed to load: {error}</p>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState
          title="No runs yet"
          description="Run history appears here after you run your first experiment. Each run captures scores, comparisons, and response details."
        />
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#222] text-[#555] text-xs">
                  <th className="pb-2 pr-3 font-normal w-6"></th>
                  <th className="text-left pb-2 pr-4 font-normal">Experiment</th>
                  <th
                    className="text-left pb-2 pr-4 font-normal cursor-pointer hover:text-[#ededed] select-none"
                    onClick={() => handleSortClick("created_at")}
                  >
                    Date {sortBy === "created_at" ? (sortOrder === "desc" ? "↓" : "↑") : ""}
                  </th>
                  <th className="text-left pb-2 pr-4 font-normal">Models (A / B)</th>
                  <th className="text-right pb-2 pr-4 font-normal">Score A</th>
                  <th className="text-right pb-2 pr-4 font-normal">Score B</th>
                  <th
                    className="text-right pb-2 pr-4 font-normal cursor-pointer hover:text-[#ededed] select-none"
                    onClick={() => handleSortClick("score_delta")}
                  >
                    Delta {sortBy === "score_delta" ? (sortOrder === "desc" ? "↓" : "↑") : ""}
                  </th>
                  <th className="text-left pb-2 pr-4 font-normal">Winner</th>
                  <th className="text-left pb-2 pr-4 font-normal">Confidence</th>
                  <th className="text-left pb-2 font-normal">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const promptKeys = Object.keys(item.prompt_models);
                  const modelA = promptKeys[0] ? item.prompt_models[promptKeys[0]] : "-";
                  const modelB = promptKeys[1] ? item.prompt_models[promptKeys[1]] : "-";
                  const metrics = item.summary_metrics;

                  const isSelected = selectedIds.includes(item.id);
                  return (
                    <tr
                      key={item.id}
                      className={`border-b border-[#1a1a1a] hover:bg-[#111] cursor-pointer transition-colors${isSelected ? " bg-[#0f1a0f]" : ""}`}
                      onClick={() => {
                        if (item.experiment_id) {
                          router.push(`/experiments/${item.experiment_id}/results/${item.id}`);
                        }
                      }}
                    >
                      <td
                        className="py-3 pr-3"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedIds((prev) => {
                            if (prev.includes(item.id)) {
                              return prev.filter((id) => id !== item.id);
                            }
                            if (prev.length >= 2) {
                              return [prev[1], item.id];
                            }
                            return [...prev, item.id];
                          });
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="accent-white cursor-pointer"
                        />
                      </td>
                      <td className="py-3 pr-4 text-[#ededed]">
                        {item.experiment_name ?? <span className="text-[#555]">—</span>}
                      </td>
                      <td className="py-3 pr-4 text-[#888] whitespace-nowrap">
                        {formatDate(item.created_at)}
                      </td>
                      <td className="py-3 pr-4 text-[#666] text-xs">
                        <span title={modelA}>{modelA.split("/").pop()}</span>
                        <span className="mx-1 text-[#444]">/</span>
                        <span title={modelB}>{modelB.split("/").pop()}</span>
                      </td>
                      <td className="py-3 pr-4 text-right text-[#888]">
                        {metrics ? metrics.score_a.toFixed(2) : <span className="text-[#444]">—</span>}
                      </td>
                      <td className="py-3 pr-4 text-right text-[#888]">
                        {metrics ? metrics.score_b.toFixed(2) : <span className="text-[#444]">—</span>}
                      </td>
                      <td className="py-3 pr-4 text-right text-[#888]">
                        {metrics ? metrics.score_delta.toFixed(2) : <span className="text-[#444]">—</span>}
                      </td>
                      <td className="py-3 pr-4 text-[#ededed]">
                        {metrics ? metrics.winner : <span className="text-[#444]">—</span>}
                      </td>
                      <td className="py-3 pr-4">
                        {metrics ? (
                          <span className={`capitalize text-xs ${confidenceBadge(metrics.confidence)}`}>
                            {metrics.confidence}
                          </span>
                        ) : (
                          <span className="text-[#444]">—</span>
                        )}
                      </td>
                      <td className="py-3">
                        <span className={`capitalize text-xs ${statusBadge(item.status)}`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center gap-4 mt-6 text-sm text-[#888]">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                className="px-3 py-1 border border-[#333] rounded disabled:opacity-30 hover:border-[#555] transition-colors"
              >
                Prev
              </button>
              <span>{currentPage} / {totalPages}</span>
              <button
                disabled={offset + LIMIT >= total}
                onClick={() => setOffset(offset + LIMIT)}
                className="px-3 py-1 border border-[#333] rounded disabled:opacity-30 hover:border-[#555] transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
