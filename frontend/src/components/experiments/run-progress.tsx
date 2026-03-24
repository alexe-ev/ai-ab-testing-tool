"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { getExportUrl } from "@/lib/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STEPS = ["running", "evaluating", "analyzing", "reporting"] as const;
type Step = (typeof STEPS)[number];

const STEP_LABELS: Record<Step, string> = {
  running: "Running prompts",
  evaluating: "Evaluating responses",
  analyzing: "Analyzing results",
  reporting: "Generating reports",
};

interface LogEntry {
  timestamp?: string;
  step?: string;
  case_id?: string;
  case_index?: number;
  total?: number;
  detail?: string;
  type?: string; // info | success | error | done
  status?: string;
  result?: Record<string, string>;
  error?: string;
}

interface RunProgressProps {
  jobId: string;
  experimentId: string;
}

export default function RunProgress({ jobId, experimentId }: RunProgressProps) {
  const [log, setLog] = useState<LogEntry[]>([]);
  const [currentStep, setCurrentStep] = useState<Step | null>(null);
  const [caseProgress, setCaseProgress] = useState<{ index: number; total: number } | null>(null);
  const [finalStatus, setFinalStatus] = useState<"done" | "failed" | null>(null);
  const [finalResult, setFinalResult] = useState<Record<string, string> | null>(null);
  const [finalError, setFinalError] = useState<string | null>(null);
  const [connectError, setConnectError] = useState<string | null>(null);
  const [startTime] = useState(() => Date.now());
  const [elapsed, setElapsed] = useState(0);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Elapsed timer
  useEffect(() => {
    if (finalStatus) return;
    const interval = setInterval(() => setElapsed(Date.now() - startTime), 1000);
    return () => clearInterval(interval);
  }, [startTime, finalStatus]);

  // SSE connection
  useEffect(() => {
    const eventSource = new EventSource(`${BASE_URL}/api/jobs/${jobId}/stream`);

    eventSource.onmessage = (event) => {
      const entry: LogEntry = JSON.parse(event.data);

      if (entry.type === "done") {
        setFinalStatus(entry.status as "done" | "failed");
        if (entry.result) setFinalResult(entry.result);
        if (entry.error) setFinalError(entry.error);
        eventSource.close();
        return;
      }

      setLog((prev) => [...prev, entry]);

      if (entry.step) {
        setCurrentStep(entry.step as Step);
      }
      if (entry.case_index && entry.total) {
        setCaseProgress({ index: entry.case_index, total: entry.total });
      }
    };

    eventSource.onerror = () => {
      setConnectError("Connection lost. Retrying...");
      // EventSource auto-reconnects
    };

    return () => eventSource.close();
  }, [jobId]);

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  const formatElapsed = (ms: number) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  if (connectError && log.length === 0) {
    return (
      <div className="p-4 border border-red-800 rounded-lg">
        <p className="text-red-400 text-sm">{connectError}</p>
      </div>
    );
  }

  if (finalStatus === "failed") {
    return (
      <div className="p-4 border border-red-800 rounded-lg space-y-3">
        <p className="text-red-400 text-sm font-medium">Run failed</p>
        {finalError && (
          <p className="text-[#888] text-xs font-mono">{finalError}</p>
        )}
        <LogPanel log={log} logEndRef={logEndRef} />
      </div>
    );
  }

  if (finalStatus === "done") {
    const runPath = finalResult?.run_path ?? "";
    const runFileName = runPath.split("/").pop() ?? "";
    const runId = runFileName.replace(/^run_/, "").replace(/\.json$/, "");

    return (
      <div className="p-4 border border-green-800 rounded-lg space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-green-400 text-sm font-medium">Run complete</p>
          <span className="text-xs text-[#555]">{formatElapsed(elapsed)}</span>
        </div>
        {runId && (
          <div className="flex items-center gap-3">
            <a
              href={getExportUrl(runId, "html")}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-4 py-2 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors"
            >
              Open Report
            </a>
            <Link
              href={`/experiments/${experimentId}/results/${runId}`}
              className="inline-block px-4 py-2 border border-[#333] text-sm rounded hover:border-[#555] transition-colors"
            >
              View Details
            </Link>
          </div>
        )}
        <LogPanel log={log} logEndRef={logEndRef} collapsed />
      </div>
    );
  }

  // In progress
  const currentStepIndex = currentStep ? STEPS.indexOf(currentStep) : -1;
  const progressPercent = caseProgress
    ? Math.round((caseProgress.index / caseProgress.total) * 100)
    : 0;

  return (
    <div className="p-4 border border-[#222] rounded-lg space-y-4">
      {/* Header with timer */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-[#ededed]">
          {currentStep ? STEP_LABELS[currentStep] : "Preparing..."}
        </p>
        <span className="text-xs text-[#555] font-mono">{formatElapsed(elapsed)}</span>
      </div>

      {/* Progress bar */}
      {caseProgress && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-[#888]">
            <span>Case {caseProgress.index} of {caseProgress.total}</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="w-full h-1.5 bg-[#222] rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Pipeline steps */}
      <div className="flex gap-3">
        {STEPS.map((step, i) => {
          const isDone = i < currentStepIndex;
          const isCurrent = i === currentStepIndex;
          return (
            <div key={step} className="flex items-center gap-1.5">
              <div
                className={[
                  "w-1.5 h-1.5 rounded-full",
                  isDone ? "bg-green-500" : isCurrent ? "bg-white animate-pulse" : "bg-[#333]",
                ].join(" ")}
              />
              <span
                className={[
                  "text-xs",
                  isDone ? "text-[#555]" : isCurrent ? "text-[#ededed]" : "text-[#444]",
                ].join(" ")}
              >
                {STEP_LABELS[step]}
              </span>
            </div>
          );
        })}
      </div>

      {/* Live log */}
      <LogPanel log={log} logEndRef={logEndRef} />
    </div>
  );
}

function LogPanel({
  log,
  logEndRef,
  collapsed = false,
}: {
  log: LogEntry[];
  logEndRef: React.RefObject<HTMLDivElement | null>;
  collapsed?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(!collapsed);

  if (log.length === 0) return null;

  return (
    <div>
      <button
        onClick={() => setIsOpen((p) => !p)}
        className="text-xs text-[#555] hover:text-[#888] transition-colors"
      >
        {isOpen ? "▾" : "▸"} Log ({log.length} entries)
      </button>
      {isOpen && (
        <div className="mt-2 max-h-48 overflow-y-auto bg-[#0a0a0a] border border-[#1a1a1a] rounded p-2 space-y-0.5">
          {log.map((entry, i) => (
            <div key={i} className="flex gap-2 text-xs font-mono">
              <span className="text-[#333] shrink-0">
                {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : ""}
              </span>
              <span
                className={
                  entry.type === "error"
                    ? "text-red-400"
                    : entry.type === "success"
                    ? "text-green-400"
                    : "text-[#888]"
                }
              >
                {entry.detail}
              </span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      )}
    </div>
  );
}
