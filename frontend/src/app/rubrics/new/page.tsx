"use client";

import { useRouter } from "next/navigation";
import RubricForm from "@/components/rubrics/rubric-form";
import { createRubric } from "@/lib/api";
import type { RubricFormData } from "@/lib/types";

export default function NewRubricPage() {
  const router = useRouter();

  async function handleSave(data: RubricFormData) {
    await createRubric(data);
    router.push("/rubrics");
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">New Rubric</h1>
      </div>
      <RubricForm onSave={handleSave} />
    </div>
  );
}
