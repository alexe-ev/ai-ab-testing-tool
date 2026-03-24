"use client";

import { useRouter } from "next/navigation";
import TestSetForm from "@/components/test-sets/test-set-form";
import { createTestSet } from "@/lib/api";
import type { TestSetFormData } from "@/lib/types";

export default function NewTestSetPage() {
  const router = useRouter();

  async function handleSave(data: TestSetFormData) {
    await createTestSet(data);
    router.push("/test-sets");
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">New Test Set</h1>
      </div>
      <TestSetForm onSave={handleSave} />
    </div>
  );
}
