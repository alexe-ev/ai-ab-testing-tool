"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { IterationChainItem } from "@/lib/types";

interface TrendChartProps {
  chain: IterationChainItem[];
}

interface ChartPoint {
  label: string;
  fullName: string;
  scoreA: number | null;
  scoreB: number | null;
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, max - 1) + "…";
}

export default function TrendChart({ chain }: TrendChartProps) {
  const points: ChartPoint[] = chain
    .filter((item) => item.last_run_metrics !== null)
    .map((item) => ({
      label: truncate(item.name, 12),
      fullName: item.name,
      scoreA: item.last_run_metrics?.score_a ?? null,
      scoreB: item.last_run_metrics?.score_b ?? null,
    }));

  if (points.length === 0) return null;

  return (
    <div className="mt-4 border border-[#222] rounded-lg p-4">
      <p className="text-xs text-[#555] mb-3">Score trend</p>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={points} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="#222" strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#555", fontSize: 11 }}
            axisLine={{ stroke: "#333" }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 5]}
            tick={{ fill: "#555", fontSize: 11 }}
            axisLine={{ stroke: "#333" }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ background: "#0a0a0a", border: "1px solid #333", borderRadius: 6 }}
            labelStyle={{ color: "#ededed", fontSize: 12 }}
            itemStyle={{ color: "#888", fontSize: 12 }}
            formatter={(value, name) => [
              value != null ? Number(value).toFixed(2) : "—",
              name === "scoreA" ? "Score A" : "Score B",
            ]}
            labelFormatter={(_label, payload) => {
              const first = payload?.[0] as { payload?: ChartPoint } | undefined;
              return first?.payload?.fullName ?? "";
            }}
          />
          <Line
            type="monotone"
            dataKey="scoreA"
            name="scoreA"
            stroke="#6b9eff"
            strokeWidth={2}
            dot={{ fill: "#6b9eff", r: 3 }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="scoreB"
            name="scoreB"
            stroke="#f97316"
            strokeWidth={2}
            dot={{ fill: "#f97316", r: 3 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="flex gap-4 mt-2">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-[#6b9eff]"></div>
          <span className="text-xs text-[#555]">Score A</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-[#f97316]"></div>
          <span className="text-xs text-[#555]">Score B</span>
        </div>
      </div>
    </div>
  );
}
