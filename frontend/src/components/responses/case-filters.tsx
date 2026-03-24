"use client";

interface CaseFiltersProps {
  categories: string[];
  categoryFilter: string;
  onCategoryChange: (v: string) => void;
  winnerFilter: string;
  onWinnerChange: (v: string) => void;
  sortBy: string;
  onSortChange: (v: string) => void;
  totalCount: number;
  filteredCount: number;
}

export default function CaseFilters({
  categories,
  categoryFilter,
  onCategoryChange,
  winnerFilter,
  onWinnerChange,
  sortBy,
  onSortChange,
  totalCount,
  filteredCount,
}: CaseFiltersProps) {
  const selectClass =
    "bg-[#0a0a0a] border border-[#333] rounded px-2 py-1 text-sm text-[#ededed] focus:outline-none focus:border-[#555]";

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={categoryFilter}
        onChange={(e) => onCategoryChange(e.target.value)}
        className={selectClass}
      >
        <option value="all">All categories</option>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <select
        value={winnerFilter}
        onChange={(e) => onWinnerChange(e.target.value)}
        className={selectClass}
      >
        <option value="all">All</option>
        <option value="prompt_a">A wins</option>
        <option value="prompt_b">B wins</option>
        <option value="tie">TIE</option>
      </select>

      <select
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
        className={selectClass}
      >
        <option value="default">Default</option>
        <option value="biggest_delta">Biggest delta</option>
        <option value="lowest_score">Lowest score</option>
      </select>

      <span className="text-xs text-[#555] ml-auto">
        Showing {filteredCount} of {totalCount} cases
      </span>
    </div>
  );
}
