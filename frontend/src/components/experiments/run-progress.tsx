"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { getJobStatus } from "@/lib/api";
import type { JobStatus } from "@/lib/types";

const STEPS = ["running", "evaluating", "analyzing", "reporting"] as const;
type Step = (typeof STEPS)[number];

const STEP_LABELS: Record<Step, string> = {
  running: "Running prompts",
  evaluating: "Evaluating responses",
  analyzing: "Analyzing results",
  reporting: "Generating reports",
};

interface RunProgressProps {
  jobId: string;
  onDone?: (job: JobStatus) => void;
}

export default function RunProgress({ jobId, onDone }: RunProgressProps) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const activeRef = useRef(true);

  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  const scheduleNext = useCallback(
    (poll: () => void) => {
      const t = setTimeout(() => {
        if (activeRef.current) poll();
      }, 2000);
      return t;
    },
    []
  );

  useEffect(() => {
    activeRef.current = true;
    let timeout: ReturnType<typeof setTimeout>;

    function poll() {
      getJobStatus(jobId)
        .then((j) => {
          if (!activeRef.current) return;
          setJob(j);
          if (j.status === "done") {
            if (onDoneRef.current) onDoneRef.current(j);
            return;
          }
          if (j.status === "failed") return;
          timeout = scheduleNext(poll);
        })
        .catch((e: unknown) => {
          if (!activeRef.current) return;
          setError(e instanceof Error ? e.message : String(e));
        });
    }

    poll();

    return () => {
      activeRef.current = false;
      clearTimeout(timeout);
    };
  }, [jobId, scheduleNext]);

  if (error) {
    return (
      <div className="p-4 border border-red-800 rounded-lg">
        <p className="text-red-400 text-sm">Failed to fetch job status: {error}</p>
      </div>
    );
  }

  if (!job) {
    return <p className="text-[#888] text-sm">Starting...</p>;
  }

  if (job.status === "failed") {
    return (
      <div className="p-4 border border-red-800 rounded-lg">
        <p className="text-red-400 text-sm font-medium mb-1">Run failed</p>
        {job.error && (
          <p className="text-[#888] text-xs font-mono">{job.error}</p>
        )}
      </div>
    );
  }

  if (job.status === "done") {
    return (
      <div className="p-4 border border-green-800 rounded-lg">
        <p className="text-green-400 text-sm font-medium">Run complete</p>
        {job.result && (
          <div className="mt-2 space-y-1">
            {Object.entries(job.result).map(([key, val]) => (
              <p key={key} className="text-[#888] text-xs font-mono">
                {key}: {val}
              </p>
            ))}
          </div>
        )}
      </div>
    );
  }

  const currentStep = job.progress?.step as Step | undefined;
  const currentStepIndex = currentStep ? STEPS.indexOf(currentStep) : -1;

  return (
    <div className="p-4 border border-[#222] rounded-lg space-y-4">
      <p className="text-sm text-[#888]">
        {job.progress?.detail ?? "Preparing..."}
      </p>
      <div className="space-y-2">
        {STEPS.map((step, i) => {
          const isDone = i < currentStepIndex;
          const isCurrent = i === currentStepIndex;
          return (
            <div key={step} className="flex items-center gap-3">
              <div
                className={[
                  "w-2 h-2 rounded-full shrink-0",
                  isDone
                    ? "bg-green-500"
                    : isCurrent
                    ? "bg-white animate-pulse"
                    : "bg-[#333]",
                ].join(" ")}
              />
              <span
                className={[
                  "text-sm",
                  isDone
                    ? "text-[#555]"
                    : isCurrent
                    ? "text-[#ededed]"
                    : "text-[#444]",
                ].join(" ")}
              >
                {STEP_LABELS[step]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
