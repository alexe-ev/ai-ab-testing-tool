"use client";

import { useRouter } from "next/navigation";
import ExperimentForm from "@/components/experiments/experiment-form";
import { apiPost } from "@/lib/api";
import type { ExperimentFormData, Experiment } from "@/lib/types";

export default function NewExperimentPage() {
  const router = useRouter();

  async function handleSave(data: ExperimentFormData) {
    await apiPost<Experiment>("/api/experiments-db/", data);
    router.push("/");
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">New Experiment</h1>
      </div>
      <ExperimentForm onSave={handleSave} />
    </div>
  );
}
