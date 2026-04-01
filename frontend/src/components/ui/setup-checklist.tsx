import Link from "next/link";

interface SetupChecklistProps {
  hasApiKeys: boolean;
  testSetCount: number;
  rubricCount: number;
  experimentCount: number;
}

interface ChecklistItem {
  label: string;
  href: string;
  done: boolean;
}

export function SetupChecklist({
  hasApiKeys,
  testSetCount,
  rubricCount,
  experimentCount,
}: SetupChecklistProps) {
  const items: ChecklistItem[] = [
    { label: "Add API keys in Settings", href: "/settings", done: hasApiKeys },
    { label: "Create a Test Set", href: "/test-sets", done: testSetCount > 0 },
    { label: "Create a Rubric", href: "/rubrics", done: rubricCount > 0 },
    { label: "Create an Experiment", href: "/experiments/new", done: experimentCount > 0 },
  ];

  const allDone = items.every((item) => item.done);
  if (allDone) return null;

  return (
    <div className="border border-[#333] rounded-lg p-4 mb-6 bg-[#111]">
      <p className="text-sm font-medium text-[#ededed] mb-3">Getting started</p>
      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li key={item.href} className="flex items-center gap-2">
            {item.done ? (
              <span className="text-green-500 text-sm leading-none">&#10003;</span>
            ) : (
              <span className="text-[#444] text-sm leading-none">&#9675;</span>
            )}
            <Link
              href={item.href}
              className={`text-sm ${item.done ? "text-[#555] line-through" : "text-[#ededed] hover:text-white"}`}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
