export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export type JobMeta = {
  job_id: string;
  filename: string;
  status: JobStatus;
  progress: number;
  stage: string;
  error: string | null;
  created_at: string;
  updated_at: string;
  result_path: string | null;
  extra: Record<string, unknown>;
};

type JobCreateResponse = {
  job_id: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parseJsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function createJob(file: File): Promise<JobCreateResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/jobs`, {
    method: "POST",
    body: form
  });
  return parseJsonOrThrow<JobCreateResponse>(res);
}

export async function getJob(jobId: string): Promise<JobMeta> {
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
  return parseJsonOrThrow<JobMeta>(res);
}

export async function getResultMarkdown(jobId: string): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}/result`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.text();
}

export function getResultDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/jobs/${jobId}/result`;
}

