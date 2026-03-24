"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Experiments" },
  { href: "/test-sets", label: "Test Sets" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r border-[#222] bg-[#0a0a0a] flex flex-col">
      <div className="px-4 py-5 border-b border-[#222]">
        <span className="text-sm font-semibold tracking-tight text-white">
          Prompt A/B
        </span>
      </div>
      <nav className="flex flex-col gap-1 p-3">
        {navItems.map(({ href, label }) => {
          const active = href === "/" ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`px-3 py-2 rounded text-sm transition-colors ${
                active
                  ? "bg-[#1a1a1a] text-white"
                  : "text-[#888] hover:text-white hover:bg-[#111]"
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
