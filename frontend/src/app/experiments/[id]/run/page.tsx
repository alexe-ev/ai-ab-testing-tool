"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  getTestSets,
  getRubrics,
  dryRunExperiment,
  runFullPipeline,
  getExperimentRuns,
  getExportUrl,
  getIterationChain,
  cloneExperiment,
  getExperiment,
} from "@/lib/api";
import type {
  TestSetListItem,
  RubricListItem,
  DryRunResult,
  RunListItem,
  IterationChainItem,
  Experiment,
} from "@/lib/types";
import ModelSelector from "@/components/experiments/model-selector";
import RunProgress from "@/components/experiments/run-progress";
import TrendChart from "@/components/experiments/trend-chart";
import Tooltip from "@/components/ui/tooltip";

const MODES = ["both", "pointwise", "pairwise"] as const;

export default function RunExperimentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [testSets, setTestSets] = useState<TestSetListItem[]>([]);
  const [rubrics, setRubrics] = useState<RubricListItem[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [testSetId, setTestSetId] = useState("");
  const [rubricId, setRubricId] = useState("");
  const [judgeModel, setJudgeModel] = useState("claude-sonnet-4-6");
  const [mode, setMode] = useState<string>("both");

  const [preview, setPreview] = useState<DryRunResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const [jobId, setJobId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [runLoading, setRunLoading] = useState(false);

  const [pastRuns, setPastRuns] = useState<RunListItem[]>([]);
  const [chain, setChain] = useState<IterationChainItem[]>([]);
  const [cloning, setCloning] = useState(false);

  useEffect(() => {
    getExperimentRuns(id).then(setPastRuns).catch(() => {});
    getIterationChain(id).then(setChain).catch(() => {});
  }, [id]);

  useEffect(() => {
    Promise.all([getTestSets(), getRubrics(), getExperiment(id)])
      .then(([ts, rubs, exp]) => {
        setTestSets(ts);
        setRubrics(rubs);
        setExperiment(exp);

        const savedTestSetId = exp.config?.test_set_id;
        if (savedTestSetId && ts.some((t) => t.id === savedTestSetId)) {
          setTestSetId(savedTestSetId);
        } else if (ts.length > 0) {
          setTestSetId(ts[0].id);
        }

        const savedRubricId = exp.config?.rubric_id;
        if (savedRubricId && rubs.some((r) => r.id === savedRubricId)) {
          setRubricId(savedRubricId);
        } else if (rubs.length > 0) {
          setRubricId(rubs[0].id);
        }
      })
      .catch((e: unknown) =>
        setLoadError(e instanceof Error ? e.message : String(e))
      )
      .finally(() => setLoadingData(false));
  }, [id]);

  async function handleDryRun() {
    if (!testSetId || !rubricId) return;
    setPreviewLoading(true);
    setPreviewError(null);
    setPreview(null);
    try {
      const result = await dryRunExperiment(id, testSetId, rubricId);
      setPreview(result);
    } catch (e: unknown) {
      setPreviewError(e instanceof Error ? e.message : String(e));
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleRun() {
    if (!testSetId || !rubricId) return;
    setRunLoading(true);
    setRunError(null);
    try {
      const resp = await runFullPipeline(id, testSetId, rubricId, judgeModel, mode);
      setJobId(resp.job_id);
    } catch (e: unknown) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunLoading(false);
    }
  }

  async function handleCloneIterate() {
    setCloning(true);
    try {
      const newExp = await cloneExperiment(id);
      router.push(`/experiments/${newExp.id}/edit`);
    } catch (e: unknown) {
      setRunError(e instanceof Error ? e.message : "Failed to clone experiment");
    } finally {
      setCloning(false);
    }
  }

  if (loadingData) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading...</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">Failed to load: {loadError}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222] flex items-center justify-between">
        <h1 className="text-xl font-semibold">Run Experiment</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleCloneIterate}
            disabled={cloning}
            className="px-3 py-1.5 border border-[#333] text-sm rounded hover:border-[#555] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {cloning ? "Cloning..." : "Clone & Iterate"}
          </button>
          <Link href="/" className="text-[#888] text-sm hover:text-[#ededed]">
            Back
          </Link>
        </div>
      </div>

      {/* Iteration chain */}
      {chain.length > 1 && (
        <div className="px-8 pt-6 pb-2">
          <h2 className="text-xs text-[#555] mb-3 uppercase tracking-wide">Iteration chain</h2>
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {chain.map((item, idx) => {
              const isCurrent = item.id === id;
              return (
                <div key={item.id} className="flex items-center gap-2 shrink-0">
                  <Link
                    href={`/experiments/${item.id}/run`}
                    className={`px-3 py-2 border rounded-lg text-xs max-w-[140px] block${
                      isCurrent
                        ? " border-[#555] bg-[#111] text-[#ededed]"
                        : " border-[#222] text-[#888] hover:border-[#444] hover:text-[#ededed]"
                    } transition-colors`}
                  >
                    <p className="truncate font-medium">{item.name}</p>
                    <p className="text-[#555] mt-0.5">
                      {item.last_run_metrics
                        ? `delta: ${item.last_run_metrics.score_delta >= 0 ? "+" : ""}${item.last_run_metrics.score_delta.toFixed(2)}`
                        : "No runs"}
                    </p>
                  </Link>
                  {idx < chain.length - 1 && (
                    <span className="text-[#444] text-sm">→</span>
                  )}
                </div>
              );
            })}
          </div>
          <TrendChart chain={chain} />
        </div>
      )}

      <div className="p-8 max-w-xl space-y-6">
        {/* Test set selector */}
        <div>
          <label className="block text-sm text-[#888] mb-1" htmlFor="test-set">
            Test Set
          </label>
          {testSets.length === 0 ? (
            <p className="text-[#555] text-sm">
              No test sets yet.{" "}
              <Link href="/test-sets" className="underline underline-offset-2">
                Create one
              </Link>
            </p>
          ) : (
            <select
              id="test-set"
              value={testSetId}
              onChange={(e) => {
                setTestSetId(e.target.value);
                setPreview(null);
              }}
              className="w-full bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
            >
              {testSets.map((ts) => (
                <option key={ts.id} value={ts.id}>
                  {ts.name} ({ts.case_count} cases)
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Rubric selector */}
        <div>
          <label className="block text-sm text-[#888] mb-1" htmlFor="rubric">
            Rubric
          </label>
          {rubrics.length === 0 ? (
            <p className="text-[#555] text-sm">
              No rubrics yet.{" "}
              <Link href="/rubrics" className="underline underline-offset-2">
                Create one
              </Link>
            </p>
          ) : (
            <select
              id="rubric"
              value={rubricId}
              onChange={(e) => {
                setRubricId(e.target.value);
                setPreview(null);
              }}
              className="w-full bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
            >
              {rubrics.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Judge model */}
        <div>
          <label className="block text-sm text-[#888] mb-1" htmlFor="judge-model">
            Judge Model
          </label>
          <ModelSelector id="judge-model" value={judgeModel} onChange={setJudgeModel} />
        </div>

        {/* Mode */}
        <div>
          <label className="block text-sm text-[#888] mb-1" htmlFor="mode">
            <Tooltip text="Pointwise: scores each response 1-5 independently. Pairwise: compares A vs B head-to-head. Both: runs both for maximum reliability.">
              Evaluation Mode
            </Tooltip>
          </label>
          <select
            id="mode"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="w-full bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
          >
            {MODES.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        {/* Dry run preview */}
        {!jobId && (
          <div>
            <button
              onClick={handleDryRun}
              disabled={previewLoading || !testSetId || !rubricId}
              className="px-4 py-2 border border-[#333] text-sm rounded hover:border-[#555] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {previewLoading ? "Checking..." : "Preview"}
            </button>

            {previewError && (
              <p className="mt-2 text-red-400 text-sm">{previewError}</p>
            )}

            {preview && (
              <div className="mt-3 p-3 border border-[#222] rounded-lg text-sm space-y-1">
                <p className="text-[#ededed] font-medium">{preview.experiment_name}</p>
                <p className="text-[#888]">
                  {preview.test_case_count} test cases · prompts:{" "}
                  {preview.prompt_names.join(", ")}
                </p>
                {Object.entries(preview.prompt_models).map(([name, model]) => (
                  <p key={name} className="text-[#888]">
                    {name}: {model}
                  </p>
                ))}
                <p className="text-[#888]">Rubric: {preview.rubric_name}</p>
              </div>
            )}
          </div>
        )}

        {/* Start run */}
        {!jobId && (
          <div>
            {runError && (
              <p className="mb-2 text-red-400 text-sm">{runError}</p>
            )}
            <button
              onClick={handleRun}
              disabled={runLoading || !testSetId || !rubricId}
              className="px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {runLoading ? "Starting..." : "Start Run"}
            </button>
          </div>
        )}

        {/* Progress */}
        {jobId && (
          <RunProgress jobId={jobId} experimentId={id} />
        )}
      </div>

      {/* Past runs */}
      {pastRuns.length > 0 && (
        <div className="px-8 pb-8">
          <h2 className="text-sm font-medium text-[#888] mb-3">Past runs</h2>
          <div className="space-y-2">
            {pastRuns.map((run) => (
              <div
                key={run.id}
                className="flex items-center justify-between p-3 border border-[#222] rounded-lg"
              >
                <div className="space-y-0.5">
                  <p className="text-sm text-[#ededed]">
                    {Object.values(run.prompt_names).join(" vs ") || run.id}
                  </p>
                  <p className="text-xs text-[#555]">
                    {run.total_cases} cases
                    {run.error_count > 0 && ` · ${run.error_count} errors`}
                    {" · "}
                    {new Date(run.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {run.status === "complete" && (
                    <>
                      <a
                        href={getExportUrl(run.id, "html")}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 text-xs border border-[#333] rounded hover:border-[#555] transition-colors"
                      >
                        Report
                      </a>
                      <Link
                        href={`/experiments/${id}/results/${run.id}`}
                        className="px-3 py-1 text-xs border border-[#333] rounded hover:border-[#555] transition-colors"
                      >
                        Details
                      </Link>
                    </>
                  )}
                  {run.status === "failed" && (
                    <span className="text-xs text-red-400">failed</span>
                  )}
                  {run.status === "running" && (
                    <span className="text-xs text-yellow-400">running</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
