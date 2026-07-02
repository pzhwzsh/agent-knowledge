export type User = {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  is_admin: boolean;
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


export type UserFeedback = {
  id: string;
  user_id: string;
  feature: string;
  feedback_type: "bug" | "repair" | "delete" | "idea" | "other";
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  status: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  user_id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
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
export const API_UNAUTHORIZED_EVENT = "personal-knowledge-radar:unauthorized";
const DEFAULT_TIMEOUT_MS = 15000;

export class ApiError extends Error {
  constructor(message: string, public status: number, public path: string) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiRequestOptions = RequestInit & {
  timeoutMs?: number;
};

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}, token?: string | null): Promise<T> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const timeoutController = new AbortController();
  const timeoutId = window.setTimeout(() => timeoutController.abort(), timeoutMs);
  const signal = mergeAbortSignals(options.signal, timeoutController.signal);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const message = await readErrorMessage(response);
      if (response.status === 401) dispatchUnauthorized();
      throw new ApiError(message, response.status, path);
    }

    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("请求超时，请稍后重试", 0, path);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function readErrorMessage(response: Response) {
  let message = `请求失败：${response.status}`;
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (typeof body.detail === "string") message = body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) message = body.detail[0].msg;
  } catch {
    // Keep status message.
  }
  return message;
}

function dispatchUnauthorized() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(API_UNAUTHORIZED_EVENT));
}

function mergeAbortSignals(left?: AbortSignal | null, right?: AbortSignal | null) {
  if (!left) return right ?? undefined;
  if (!right) return left;
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (left.aborted || right.aborted) {
    controller.abort();
  } else {
    left.addEventListener("abort", abort, { once: true });
    right.addEventListener("abort", abort, { once: true });
  }
  return controller.signal;
}

export function isLikelyUrl(value: string) {
  return /^https?:\/\//i.test(value.trim());
}
