"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  getTestSets,
  getRubrics,
  dryRunExperiment,
  runFullPipeline,
} from "@/lib/api";
import type {
  TestSetListItem,
  RubricListItem,
  DryRunResult,
  JobStatus,
} from "@/lib/types";
import ModelSelector, { MODELS } from "@/components/experiments/model-selector";
import RunProgress from "@/components/experiments/run-progress";

const MODES = ["both", "pointwise", "pairwise"] as const;

export default function RunExperimentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const [testSets, setTestSets] = useState<TestSetListItem[]>([]);
  const [rubrics, setRubrics] = useState<RubricListItem[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [testSetId, setTestSetId] = useState("");
  const [rubricId, setRubricId] = useState("");
  const [judgeModel, setJudgeModel] = useState(MODELS[4]); // claude-sonnet
  const [mode, setMode] = useState<string>("both");

  const [preview, setPreview] = useState<DryRunResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const [jobId, setJobId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [runLoading, setRunLoading] = useState(false);

  useEffect(() => {
    Promise.all([getTestSets(), getRubrics()])
      .then(([ts, rubs]) => {
        setTestSets(ts);
        setRubrics(rubs);
        if (ts.length > 0) setTestSetId(ts[0].id);
        if (rubs.length > 0) setRubricId(rubs[0].id);
      })
      .catch((e: unknown) =>
        setLoadError(e instanceof Error ? e.message : String(e))
      )
      .finally(() => setLoadingData(false));
  }, []);

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

  function handleJobDone(_job: JobStatus) {
    // Job is complete; RunProgress shows results
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
        <Link href="/" className="text-[#888] text-sm hover:text-[#ededed]">
          Back
        </Link>
      </div>

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
            Evaluation Mode
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
          <RunProgress jobId={jobId} onDone={handleJobDone} />
        )}
      </div>
    </div>
  );
}
