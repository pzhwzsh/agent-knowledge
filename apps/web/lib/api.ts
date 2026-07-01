export type User = {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type DocumentItem = {
  id: string;
  title: string;
  source_url: string | null;
  source_type: string;
  category: string;
  summary: string | null;
  long_summary: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
};

export type DocumentChunk = {
  id: string;
  user_id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  embedding: number[] | null;
  metadata_json: Record<string, unknown>;
};

export type DocumentWithChunks = DocumentItem & {
  chunks: DocumentChunk[];
};

export type Recommendation = {
  id: string;
  user_id: string;
  content_id: string;
  score: number;
  category: string;
  summary: string | null;
  reason: string | null;
  tags: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type IngestionJob = {
  id: string;
  user_id: string;
  input_type: "url" | "text";
  input_value: string;
  status: string;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
  finished_at: string | null;
};

export type IngestionQueueResponse = {
  job: IngestionJob;
  task_id: string | null;
};

export type SearchResult = {
  chunk_id: string;
  document_id: string;
  title: string;
  source_url: string | null;
  content: string;
  score: number;
};

export type ChatResponse = {
  answer: string;
  citations: { document_id: string; title: string; source_url: string | null; chunk_id: string }[];
  related_documents: SearchResult[];
};

export type Preference = {
  id: string;
  user_id: string;
  interests: string[];
  negative_interests: string[];
  enabled_categories: string[];
  push_channel: string;
  push_email: string | null;
  dingtalk_webhook: string | null;
  push_time: string;
  daily_limit: number;
  language_preferences: Record<string, unknown>;
};

type ApiErrorBody = {
  detail?: string | { msg?: string }[];
};

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function apiRequest<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `请求失败：${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (typeof body.detail === "string") message = body.detail;
      if (Array.isArray(body.detail) && body.detail[0]?.msg) message = body.detail[0].msg;
    } catch {
      // Keep status message.
    }
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function isLikelyUrl(value: string) {
  return /^https?:\/\//i.test(value.trim());
}
