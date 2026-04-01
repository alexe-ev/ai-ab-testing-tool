import Link from "next/link";

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  secondaryText?: string;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  secondaryText,
}: EmptyStateProps) {
  return (
    <div className="border border-[#222] rounded-lg p-12 text-center">
      <p className="text-lg text-white font-medium mb-2">{title}</p>
      <p className="text-sm text-[#888] mb-6 max-w-md mx-auto">{description}</p>
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="inline-block px-4 py-2 bg-white text-black text-sm rounded border border-white hover:bg-[#e0e0e0] transition-colors"
        >
          {actionLabel}
        </Link>
      )}
      {secondaryText && (
        <p className="text-xs text-[#555] mt-4">{secondaryText}</p>
      )}
    </div>
  );
}
