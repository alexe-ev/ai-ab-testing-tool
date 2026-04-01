"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { compareRuns } from "@/lib/api";
import type { CompareData, AnalysisData } from "@/lib/types";

function DeltaIndicator({ a, b, higherIsBetter = true }: { a: number; b: number; higherIsBetter?: boolean }) {
  const diff = b - a;
  const better = higherIsBetter ? diff > 0 : diff < 0;
  const worse = higherIsBetter ? diff < 0 : diff > 0;
  if (better) return <span className="text-green-400 text-xs ml-1">B better</span>;
  if (worse) return <span className="text-red-400 text-xs ml-1">A better</span>;
  return <span className="text-[#666] text-xs ml-1">tie</span>;
}

interface RunColumnProps {
  label: string;
  analysis: AnalysisData;
  runId: string;
}

function RunColumn({ label, analysis, runId }: RunColumnProps) {
  const rec = analysis.recommendation;
  const overall = analysis.pointwise.overall_weighted;
  const promptA = analysis.prompt_a.name;
  const promptB = analysis.prompt_b.name;
  const scoreA = typeof overall[promptA] === "number" ? (overall[promptA] as number) : null;
  const scoreB = typeof overall[promptB] === "number" ? (overall[promptB] as number) : null;

  return (
    <div className="flex-1 min-w-0">
      <div className="border border-[#222] rounded-lg p-4 space-y-4">
        <div>
          <p className="text-xs text-[#555] mb-0.5">{label}</p>
          <p className="text-[#ededed] text-sm font-medium truncate">{runId}</p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-[#555]">Winner</p>
          <p className="text-[#ededed] text-sm">{rec.winner}</p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-[#555]">Confidence</p>
          <p className="text-[#ededed] text-sm capitalize">{rec.confidence}</p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-[#555]">Scores</p>
          <p className="text-[#888] text-sm">
            {promptA}: {scoreA !== null ? scoreA.toFixed(2) : "—"} &nbsp; {promptB}: {scoreB !== null ? scoreB.toFixed(2) : "—"}
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-[#555]">Models</p>
          <p className="text-[#888] text-xs">
            {promptA}: {analysis.operational_metrics?.per_prompt[promptA]?.model ?? "—"}
          </p>
          <p className="text-[#888] text-xs">
            {promptB}: {analysis.operational_metrics?.per_prompt[promptB]?.model ?? "—"}
          </p>
        </div>

        {analysis.pairwise && (
          <div className="space-y-1">
            <p className="text-xs text-[#555]">Pairwise Win Rates</p>
            <p className="text-[#888] text-xs">
              {promptA} wins: {typeof analysis.pairwise[`${promptA}_wins`] === "number"
                ? `${((analysis.pairwise[`${promptA}_wins`] as number) / analysis.pairwise.total * 100).toFixed(0)}%`
                : "—"}
            </p>
            <p className="text-[#888] text-xs">
              {promptB} wins: {typeof analysis.pairwise[`${promptB}_wins`] === "number"
                ? `${((analysis.pairwise[`${promptB}_wins`] as number) / analysis.pairwise.total * 100).toFixed(0)}%`
                : "—"}
            </p>
          </div>
        )}

        {analysis.operational_metrics && (
          <div className="space-y-1">
            <p className="text-xs text-[#555]">Operational</p>
            {[promptA, promptB].map((p) => {
              const m = analysis.operational_metrics?.per_prompt[p];
              if (!m) return null;
              return (
                <p key={p} className="text-[#888] text-xs">
                  {p}: avg {m.latency.avg.toFixed(2)}s · ${m.cost_usd.toFixed(4)}
                </p>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function DimensionComparisonTable({ analysisA, analysisB }: { analysisA: AnalysisData; analysisB: AnalysisData }) {
  const dimsA = analysisA.pointwise.dimensions;
  const dimsB = analysisB.pointwise.dimensions;
  const allDims = Array.from(new Set([...Object.keys(dimsA), ...Object.keys(dimsB)]));

  const promptAa = analysisA.prompt_a.name;
  const promptAb = analysisA.prompt_b.name;
  const promptBa = analysisB.prompt_a.name;
  const promptBb = analysisB.prompt_b.name;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-[#222] text-[#555] text-xs">
            <th className="text-left pb-2 pr-4 font-normal">Dimension</th>
            <th className="text-right pb-2 pr-4 font-normal">Run A: {promptAa}</th>
            <th className="text-right pb-2 pr-4 font-normal">Run A: {promptAb}</th>
            <th className="text-right pb-2 pr-4 font-normal">Run B: {promptBa}</th>
            <th className="text-right pb-2 font-normal">Run B: {promptBb}</th>
          </tr>
        </thead>
        <tbody>
          {allDims.map((dim) => {
            const dA = dimsA[dim];
            const dB = dimsB[dim];
            const getScore = (d: typeof dA, key: string) => {
              if (!d) return null;
              const entry = d[key];
              if (entry && typeof entry === "object" && "mean" in entry) {
                return (entry as { mean: number }).mean;
              }
              return null;
            };
            const sAa = getScore(dA, promptAa);
            const sAb = getScore(dA, promptAb);
            const sBa = getScore(dB, promptBa);
            const sBb = getScore(dB, promptBb);
            return (
              <tr key={dim} className="border-b border-[#1a1a1a]">
                <td className="py-2 pr-4 text-[#ededed]">{dim}</td>
                <td className="py-2 pr-4 text-right text-[#888]">{sAa !== null ? sAa.toFixed(2) : "—"}</td>
                <td className="py-2 pr-4 text-right text-[#888]">{sAb !== null ? sAb.toFixed(2) : "—"}</td>
                <td className="py-2 pr-4 text-right text-[#888]">{sBa !== null ? sBa.toFixed(2) : "—"}</td>
                <td className="py-2 text-right text-[#888]">{sBb !== null ? sBb.toFixed(2) : "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SummaryDelta({ analysisA, analysisB }: { analysisA: AnalysisData; analysisB: AnalysisData }) {
  const overallA = analysisA.pointwise.overall_weighted;
  const overallB = analysisB.pointwise.overall_weighted;

  const getTopScore = (overall: typeof overallA, analysis: AnalysisData) => {
    const pa = analysis.prompt_a.name;
    const pb = analysis.prompt_b.name;
    const sa = typeof overall[pa] === "number" ? (overall[pa] as number) : 0;
    const sb = typeof overall[pb] === "number" ? (overall[pb] as number) : 0;
    return Math.max(sa, sb);
  };

  const scoreA = getTopScore(overallA, analysisA);
  const scoreB = getTopScore(overallB, analysisB);
  const delta = scoreB - scoreA;

  return (
    <div className="flex gap-6 p-4 border border-[#222] rounded-lg">
      <div>
        <p className="text-xs text-[#555]">Run A best score</p>
        <p className="text-[#ededed] text-lg font-medium">{scoreA.toFixed(2)}</p>
      </div>
      <div className="text-[#333] self-center text-lg">vs</div>
      <div>
        <p className="text-xs text-[#555]">Run B best score</p>
        <p className="text-[#ededed] text-lg font-medium">{scoreB.toFixed(2)}</p>
      </div>
      <div className="self-center">
        <DeltaIndicator a={scoreA} b={scoreB} />
        <p className="text-xs text-[#555]">
          {delta >= 0 ? "+" : ""}{delta.toFixed(2)}
        </p>
      </div>
    </div>
  );
}

export default function ComparePage() {
  const searchParams = useSearchParams();
  const runAId = searchParams.get("a");
  const runBId = searchParams.get("b");

  const missingParams = !runAId || !runBId;
  const [data, setData] = useState<CompareData | null>(null);
  const [loading, setLoading] = useState(!missingParams);
  const [error, setError] = useState<string | null>(
    missingParams ? "Two run IDs required (a and b query params)." : null
  );

  useEffect(() => {
    if (missingParams || !runAId || !runBId) return;
    compareRuns(runAId, runBId)
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
        setLoading(false);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runAId, runBId]);

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading comparison...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Link href="/history" className="text-[#888] text-sm hover:text-[#ededed] mb-6 inline-block">
          Back to history
        </Link>
        <p className="text-red-400 text-sm mt-4">Error: {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">No data.</p>
      </div>
    );
  }

  const analysisA = data.run_a.analysis?.analysis;
  const analysisB = data.run_b.analysis?.analysis;

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222] flex items-center justify-between">
        <h1 className="text-xl font-semibold">Compare Runs</h1>
        <Link href="/history" className="text-[#888] text-sm hover:text-[#ededed]">
          Back to history
        </Link>
      </div>

      <div className="p-8 space-y-6 max-w-5xl">
        {analysisA && analysisB && (
          <SummaryDelta analysisA={analysisA} analysisB={analysisB} />
        )}

        <div className="flex gap-6">
          {analysisA ? (
            <RunColumn label="Run A" analysis={analysisA} runId={data.run_a.run_id} />
          ) : (
            <div className="flex-1 border border-[#222] rounded-lg p-4 text-[#555] text-sm">Run A: no analysis data</div>
          )}
          {analysisB ? (
            <RunColumn label="Run B" analysis={analysisB} runId={data.run_b.run_id} />
          ) : (
            <div className="flex-1 border border-[#222] rounded-lg p-4 text-[#555] text-sm">Run B: no analysis data</div>
          )}
        </div>

        {analysisA && analysisB && (
          <div>
            <h2 className="text-sm font-medium text-[#888] mb-3">Per-dimension scores</h2>
            <DimensionComparisonTable analysisA={analysisA} analysisB={analysisB} />
          </div>
        )}
      </div>
    </div>
  );
}
