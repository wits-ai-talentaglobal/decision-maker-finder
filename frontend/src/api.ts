import type { BatchEstimate, ClearJobsResult, Company, Job } from "./types";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export async function submitJobs(
  urlsText: string,
  confirmed: boolean
): Promise<Job[] | BatchEstimate> {
  const response = await fetch("/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls_text: urlsText, confirmed }),
  });
  return handleResponse<Job[] | BatchEstimate>(response);
}

export async function fetchJobs(): Promise<Job[]> {
  const response = await fetch("/jobs");
  return handleResponse<Job[]>(response);
}

export async function fetchCompanies(): Promise<Company[]> {
  const response = await fetch("/companies");
  return handleResponse<Company[]>(response);
}

export async function clearJobs(): Promise<ClearJobsResult> {
  const response = await fetch("/jobs", { method: "DELETE" });
  return handleResponse<ClearJobsResult>(response);
}

export function isBatchEstimate(result: Job[] | BatchEstimate): result is BatchEstimate {
  return "requires_confirmation" in result;
}
