import type { TestSet, TestSetListItem, TestSetFormData } from "./types";

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
