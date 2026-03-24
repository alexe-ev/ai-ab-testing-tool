"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import TestSetForm from "@/components/test-sets/test-set-form";
import { getTestSet, updateTestSet } from "@/lib/api";
import type { TestSet, TestSetFormData } from "@/lib/types";
import type { EditableCase } from "@/components/test-sets/test-case-table";

function apiCasesToEditable(cases: TestSet["cases"]): EditableCase[] {
  return cases.map((c, i) => ({
    _key: `loaded-${c.id}-${i}`,
    case_identifier: c.case_identifier,
    category: c.category,
    input: c.input,
    context: c.context ?? "",
    reference: c.reference ?? "",
  }));
}

export default function EditTestSetPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [testSet, setTestSet] = useState<TestSet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTestSet(id)
      .then(setTestSet)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleSave(data: TestSetFormData) {
    await updateTestSet(id, data);
    router.push("/test-sets");
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-[#888] text-sm">Loading...</p>
      </div>
    );
  }

  if (error || !testSet) {
    return (
      <div className="p-8">
        <p className="text-red-400 text-sm">
          {error ?? "Test set not found."}
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-8 pt-8 pb-4 border-b border-[#222]">
        <h1 className="text-xl font-semibold">Edit Test Set</h1>
      </div>
      <TestSetForm
        initial={{
          name: testSet.name,
          cases: apiCasesToEditable(testSet.cases),
        }}
        onSave={handleSave}
      />
    </div>
  );
}
