"use client";

interface CaseNavProps {
  currentIndex: number;
  totalCount: number;
  onPrev: () => void;
  onNext: () => void;
}

export default function CaseNav({ currentIndex, totalCount, onPrev, onNext }: CaseNavProps) {
  return (
    <div className="flex items-center gap-4">
      <button
        onClick={onPrev}
        disabled={currentIndex === 0}
        className="px-3 py-1.5 text-sm border border-[#333] rounded text-[#888] hover:text-[#ededed] hover:border-[#555] disabled:opacity-30 disabled:cursor-not-allowed"
      >
        &larr; Prev
      </button>
      <span className="text-sm text-[#888]">
        Case {currentIndex + 1} of {totalCount}
      </span>
      <button
        onClick={onNext}
        disabled={currentIndex >= totalCount - 1}
        className="px-3 py-1.5 text-sm border border-[#333] rounded text-[#888] hover:text-[#ededed] hover:border-[#555] disabled:opacity-30 disabled:cursor-not-allowed"
      >
        Next &rarr;
      </button>
      <span className="text-xs text-[#555]">Arrow keys to navigate</span>
    </div>
  );
}
