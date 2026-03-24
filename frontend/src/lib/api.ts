import type {
  TestSet, TestSetListItem, TestSetFormData,
  Rubric, RubricListItem, RubricFormData,
  ExperimentListItem,
  DryRunResult, JobStatus,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${options.method ?? "GET"} ${path} failed (${res.status}): ${text}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return apiFetch<T>(path, { method: "GET" });
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export function apiDelete(path: string): Promise<void> {
  return apiFetch<void>(path, { method: "DELETE" });
}

export function getTestSets(): Promise<TestSetListItem[]> {
  return apiGet<TestSetListItem[]>("/api/test-sets/");
}

export function getTestSet(id: string): Promise<TestSet> {
  return apiGet<TestSet>(`/api/test-sets/${id}`);
}

export function createTestSet(data: TestSetFormData): Promise<TestSet> {
  return apiPost<TestSet>("/api/test-sets/", data);
}

export function updateTestSet(id: string, data: TestSetFormData): Promise<TestSet> {
  return apiPut<TestSet>(`/api/test-sets/${id}`, data);
}

export function deleteTestSet(id: string): Promise<void> {
  return apiDelete(`/api/test-sets/${id}`);
}

export function getRubrics(): Promise<RubricListItem[]> {
  return apiGet<RubricListItem[]>("/api/rubrics/");
}

export function getRubric(id: string): Promise<Rubric> {
  return apiGet<Rubric>(`/api/rubrics/${id}`);
}

export function createRubric(data: RubricFormData): Promise<Rubric> {
  return apiPost<Rubric>("/api/rubrics/", data);
}

export function updateRubric(id: string, data: RubricFormData): Promise<Rubric> {
  return apiPut<Rubric>(`/api/rubrics/${id}`, data);
}

export function deleteRubric(id: string): Promise<void> {
  return apiDelete(`/api/rubrics/${id}`);
}

export function getExperiments(): Promise<ExperimentListItem[]> {
  return apiGet<ExperimentListItem[]>("/api/experiments-db/");
}

export function dryRunExperiment(
  experimentId: string,
  testSetId: string,
  rubricId: string,
): Promise<DryRunResult> {
  return apiPost<DryRunResult>(`/api/experiments-db/${experimentId}/dry-run`, {
    test_set_id: testSetId,
    rubric_id: rubricId,
  });
}

export function runFullPipeline(
  experimentId: string,
  testSetId: string,
  rubricId: string,
  judgeModel: string,
  mode: string,
): Promise<{ job_id: string; status: string }> {
  return apiPost<{ job_id: string; status: string }>(
    `/api/experiments-db/${experimentId}/run-full`,
    {
      test_set_id: testSetId,
      rubric_id: rubricId,
      judge_model: judgeModel,
      mode,
    },
  );
}

export function getJobStatus(jobId: string): Promise<JobStatus> {
  return apiGet<JobStatus>(`/api/jobs/${jobId}`);
}
