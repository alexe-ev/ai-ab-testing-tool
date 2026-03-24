"use client";

import type { OperationalMetrics } from "@/lib/types";

interface OperationalMetricsProps {
  metrics: OperationalMetrics;
  promptA: string;
  promptB: string;
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-[#888]">{label}</span>
      <span className="text-[#ededed]">{value}</span>
    </div>
  );
}

export default function OperationalMetricsPanel({
  metrics,
  promptA,
  promptB,
}: OperationalMetricsProps) {
  const { per_prompt, multi_variable_warning } = metrics;

  const prompts = [promptA, promptB];

  return (
    <div className="border border-[#222] rounded-lg overflow-hidden">
      <p className="px-4 py-3 text-sm text-[#888] font-medium border-b border-[#222]">
        Operational Metrics
      </p>

      {multi_variable_warning && (
        <div className="px-4 py-2 bg-yellow-950/40 border-b border-yellow-800/40 text-xs text-yellow-300">
          Warning: prompts use different models. Cost and latency are not directly comparable.
        </div>
      )}

      <div className="grid grid-cols-2 divide-x divide-[#222]">
        {prompts.map((name) => {
          const m = per_prompt[name];
          if (!m) {
            return (
              <div key={name} className="p-4">
                <p className="text-sm font-medium text-[#ededed] mb-3">{name}</p>
                <p className="text-xs text-[#555]">No data</p>
              </div>
            );
          }
          return (
            <div key={name} className="p-4 space-y-2">
              <p className="text-sm font-medium text-[#ededed]">{name}</p>
              <p className="text-xs text-[#555] font-mono mb-2">{m.model}</p>
              <MetricRow label="Responses" value={String(m.n_responses)} />
              <MetricRow label="Latency avg" value={`${m.latency.avg.toFixed(1)}s`} />
              <MetricRow label="Latency p50" value={`${m.latency.p50.toFixed(1)}s`} />
              <MetricRow label="Latency p95" value={`${m.latency.p95.toFixed(1)}s`} />
              <MetricRow label="Tokens in" value={String(m.tokens.total_input)} />
              <MetricRow label="Tokens out" value={String(m.tokens.total_output)} />
              <MetricRow label="Cost" value={`$${m.cost_usd.toFixed(4)}`} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
