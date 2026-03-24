"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import RubricForm from "@/components/rubrics/rubric-form";
import { getRubric, updateRubric } from "@/lib/api";
import type { Rubric, RubricFormData, RubricDimensionFormData } from "@/lib/types";

function apiDimensionsToForm(dimensions: Rubric["dimensions"]): RubricDimensionFormData[] {
  return dimensions.map((d) => ({
    name: d.name,
    description: d.description,
    weight: d.weight,
    levels: d.levels.map((l) => ({ score: l.score, description: l.description })),
  }));
}

export default function EditRubricPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRubric(id)
      .then(setRubric)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleSave(data: RubricFormData) {
    await updateRubric(id, data);
    router.push("/rubrics");
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading...</p>
      </div>
    );
  }

  if (error || !rubric) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">
          {error ?? "Rubric not found."}
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">Edit Rubric</h1>
      </div>
      <RubricForm
        initial={{
          name: rubric.name,
          dimensions: apiDimensionsToForm(rubric.dimensions),
        }}
        onSave={handleSave}
      />
    </div>
  );
}
