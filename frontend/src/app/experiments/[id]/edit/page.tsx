"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ExperimentForm, { DEFAULT_FORM } from "@/components/experiments/experiment-form";
import { apiGet, apiPut } from "@/lib/api";
import type { Experiment, ExperimentFormData } from "@/lib/types";

export default function EditExperimentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Experiment>(`/api/experiments-db/${id}`)
      .then(setExperiment)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleSave(data: ExperimentFormData) {
    await apiPut<Experiment>(`/api/experiments-db/${id}`, data);
    router.push("/");
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading...</p>
      </div>
    );
  }

  if (error || !experiment) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">
          {error ?? "Experiment not found."}
        </p>
      </div>
    );
  }

  const initial: ExperimentFormData = {
    name: experiment.name,
    description: experiment.description,
    hypothesis: experiment.hypothesis,
    config: experiment.config ?? DEFAULT_FORM.config,
  };

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">Edit Experiment</h1>
      </div>
      <ExperimentForm initial={initial} onSave={handleSave} />
    </div>
  );
}
