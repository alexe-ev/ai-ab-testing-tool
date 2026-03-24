"use client";

import { useEffect, useState } from "react";
import { getSettings, updateSetting, deleteSetting } from "@/lib/api";
import type { SettingItem } from "@/lib/types";

const KEY_LABELS: Record<string, string> = {
  OPENAI_API_KEY: "OpenAI API Key",
  ANTHROPIC_API_KEY: "Anthropic API Key",
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [saveMsg, setSaveMsg] = useState<Record<string, string>>({});

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : String(e))
      )
      .finally(() => setLoading(false));
  }, []);

  async function handleSave(key: string) {
    const value = editing[key];
    if (!value?.trim()) return;
    setSaving(key);
    setSaveMsg({});
    try {
      const updated = await updateSetting(key, value.trim());
      setSettings((prev) =>
        prev.map((s) => (s.key === key ? updated : s))
      );
      setEditing((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      setSaveMsg({ [key]: "Saved" });
      setTimeout(() => setSaveMsg({}), 2000);
    } catch (e: unknown) {
      setSaveMsg({ [key]: e instanceof Error ? e.message : "Failed to save" });
    } finally {
      setSaving(null);
    }
  }

  async function handleDelete(key: string) {
    setSaving(key);
    try {
      await deleteSetting(key);
      setSettings((prev) =>
        prev.map((s) =>
          s.key === key ? { ...s, value: "", is_set: false } : s
        )
      );
      setEditing((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    } catch (e: unknown) {
      setSaveMsg({ [key]: e instanceof Error ? e.message : "Failed to delete" });
    } finally {
      setSaving(null);
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">Failed to load settings: {error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-[#888] mt-1">
          API keys for LLM providers. Stored in the database, loaded on server start.
        </p>
      </div>

      <div className="p-8 max-w-xl space-y-6">
        {settings.map((setting) => {
          const isEditing = setting.key in editing;
          return (
            <div key={setting.key} className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm text-[#888]">
                  {KEY_LABELS[setting.key] ?? setting.key}
                </label>
                {setting.is_set && (
                  <span className="text-xs text-green-500">configured</span>
                )}
              </div>

              {setting.is_set && !isEditing ? (
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-[#ededed] bg-[#111] border border-[#333] rounded px-3 py-1.5 flex-1">
                    {setting.value}
                  </span>
                  <button
                    onClick={() => setEditing((p) => ({ ...p, [setting.key]: "" }))}
                    className="px-3 py-1.5 text-sm border border-[#333] rounded hover:border-[#555] transition-colors"
                  >
                    Change
                  </button>
                  <button
                    onClick={() => handleDelete(setting.key)}
                    disabled={saving === setting.key}
                    className="px-3 py-1.5 text-sm border border-red-800 text-red-400 rounded hover:border-red-600 transition-colors disabled:opacity-40"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <input
                    type="password"
                    placeholder={`Enter ${KEY_LABELS[setting.key] ?? setting.key}`}
                    value={editing[setting.key] ?? ""}
                    onChange={(e) =>
                      setEditing((p) => ({ ...p, [setting.key]: e.target.value }))
                    }
                    className="flex-1 bg-[#111] border border-[#333] rounded px-3 py-1.5 text-sm text-[#ededed] font-mono focus:outline-none focus:border-[#555]"
                  />
                  <button
                    onClick={() => handleSave(setting.key)}
                    disabled={saving === setting.key || !editing[setting.key]?.trim()}
                    className="px-4 py-1.5 bg-white text-black text-sm rounded hover:bg-[#e0e0e0] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {saving === setting.key ? "Saving..." : "Save"}
                  </button>
                  {setting.is_set && (
                    <button
                      onClick={() =>
                        setEditing((p) => {
                          const next = { ...p };
                          delete next[setting.key];
                          return next;
                        })
                      }
                      className="px-3 py-1.5 text-sm text-[#888] hover:text-[#ededed] transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              )}

              {saveMsg[setting.key] && (
                <p
                  className={`text-xs ${
                    saveMsg[setting.key] === "Saved"
                      ? "text-green-500"
                      : "text-red-400"
                  }`}
                >
                  {saveMsg[setting.key]}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
