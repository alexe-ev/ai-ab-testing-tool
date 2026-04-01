import type {
  TestSet, TestSetListItem, TestSetFormData,
  Rubric, RubricListItem, RubricFormData,
  Experiment, ExperimentListItem, IterationChainItem,
  DryRunResult, JobStatus,
  RunListItem, RunResultsData, RunHistoryResponse,
  CompareData,
  SettingItem,
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

export function getExperiment(id: string): Promise<Experiment> {
  return apiGet<Experiment>(`/api/experiments-db/${id}`);
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

export function getExperimentRuns(experimentId: string): Promise<RunListItem[]> {
  return apiGet<RunListItem[]>(`/api/experiments-db/${experimentId}/runs`);
}

export function getRunResults(runId: string): Promise<RunResultsData> {
  return apiGet<RunResultsData>(`/api/runs/${runId}/results`);
}

export function getExportUrl(runId: string, format: "html" | "markdown" | "json"): string {
  return `${BASE_URL}/api/runs/${runId}/export/${format}`;
}

export function getRunHistory(params?: {
  experiment_id?: string;
  status?: string;
  model?: string;
  sort_by?: string;
  sort_order?: string;
  limit?: number;
  offset?: number;
}): Promise<RunHistoryResponse> {
  const qs = new URLSearchParams();
  if (params) {
    if (params.experiment_id) qs.set("experiment_id", params.experiment_id);
    if (params.status) qs.set("status", params.status);
    if (params.model) qs.set("model", params.model);
    if (params.sort_by) qs.set("sort_by", params.sort_by);
    if (params.sort_order) qs.set("sort_order", params.sort_order);
    if (params.limit !== undefined) qs.set("limit", String(params.limit));
    if (params.offset !== undefined) qs.set("offset", String(params.offset));
  }
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return apiGet<RunHistoryResponse>(`/api/runs/${query}`);
}

export function cloneExperiment(id: string, name?: string): Promise<Experiment> {
  return apiPost<Experiment>(`/api/experiments-db/${id}/clone`, { name: name ?? null });
}

export function getIterationChain(id: string): Promise<IterationChainItem[]> {
  return apiGet<IterationChainItem[]>(`/api/experiments-db/${id}/chain`);
}

export function compareRuns(runA: string, runB: string): Promise<CompareData> {
  return apiGet<CompareData>(`/api/runs/compare?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`);
}

export function getSettings(): Promise<SettingItem[]> {
  return apiGet<SettingItem[]>("/api/settings/");
}

export function updateSetting(key: string, value: string): Promise<SettingItem> {
  return apiPut<SettingItem>("/api/settings/", { key, value });
}

export function deleteSetting(key: string): Promise<void> {
  return apiDelete(`/api/settings/${key}`);
}
