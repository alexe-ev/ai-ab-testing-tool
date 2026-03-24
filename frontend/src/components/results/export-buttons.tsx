"use client";

import { getExportUrl } from "@/lib/api";

interface ExportButtonsProps {
  runId: string;
}

export default function ExportButtons({ runId }: ExportButtonsProps) {
  return (
    <div className="p-5 border border-[#222] rounded-lg">
      <p className="text-sm text-[#888] font-medium mb-3">Export</p>
      <div className="flex gap-2 flex-wrap">
        <a
          href={getExportUrl(runId, "html")}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1.5 border border-[#333] text-sm rounded hover:border-[#555] transition-colors text-[#ededed]"
        >
          HTML Report
        </a>
        <a
          href={getExportUrl(runId, "markdown")}
          download
          className="px-3 py-1.5 border border-[#333] text-sm rounded hover:border-[#555] transition-colors text-[#ededed]"
        >
          Markdown
        </a>
        <a
          href={getExportUrl(runId, "json")}
          download
          className="px-3 py-1.5 border border-[#333] text-sm rounded hover:border-[#555] transition-colors text-[#ededed]"
        >
          Summary JSON
        </a>
      </div>
    </div>
  );
}
