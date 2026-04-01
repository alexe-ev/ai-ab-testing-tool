"use client";

import { useState } from "react";

interface TooltipProps {
  text: string;
  children?: React.ReactNode;
}

export default function Tooltip({ text, children }: TooltipProps) {
  const [visible, setVisible] = useState(false);

  return (
    <span className="inline-flex items-center">
      {children}
      <span
        className="relative inline-flex items-center"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
      >
        <span className="text-[10px] text-[#555] hover:text-[#888] cursor-help ml-1 inline-flex items-center justify-center w-3.5 h-3.5 rounded-full border border-[#444]">
          ?
        </span>
        {visible && (
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 bg-[#1a1a1a] border border-[#333] text-[#ccc] text-xs rounded px-3 py-2 max-w-xs w-max pointer-events-none">
            {text}
          </span>
        )}
      </span>
    </span>
  );
}
