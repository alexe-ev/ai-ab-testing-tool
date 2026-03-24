"use client";

const MODELS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4.1",
  "gpt-4.1-mini",
  "claude-sonnet",
  "claude-haiku",
  "claude-opus",
];

interface ModelSelectorProps {
  value: string;
  onChange: (value: string) => void;
  id?: string;
}

export default function ModelSelector({ value, onChange, id }: ModelSelectorProps) {
  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#555]"
    >
      {MODELS.map((m) => (
        <option key={m} value={m}>
          {m}
        </option>
      ))}
    </select>
  );
}

export { MODELS };
