/**
 * Low-level fetch wrapper shared by every backend API call.
 *
 * The backend defines no request timeout, so the client owns one via
 * AbortController. Non-2xx responses are mapped onto a discriminated
 * union so callers never need to inspect `Response` objects directly.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type ApiResult<T> =
  | { kind: "ok"; data: T }
  | { kind: "validationError"; detail: unknown }
  | { kind: "serverError"; detail: string }
  | { kind: "networkError"; message: string }
  | { kind: "timeout" };

/** Failure variants of ApiResult, independent of the success payload type. */
export type ApiFailureResult = Exclude<ApiResult<unknown>, { kind: "ok" }>;

interface RequestOptions {
  method: "GET" | "POST";
  path: string;
  body?: unknown;
  timeoutMs: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function safeParseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

export async function request<T>({
  method,
  path,
  body,
  timeoutMs,
}: RequestOptions): Promise<ApiResult<T>> {
  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers:
        body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (response.ok) {
      const data = (await safeParseJson(response)) as T;
      return { kind: "ok", data };
    }

    const parsedBody = await safeParseJson(response);
    const detail = isRecord(parsedBody) ? parsedBody.detail : undefined;

    if (response.status === 400 || response.status === 422) {
      return { kind: "validationError", detail: detail ?? parsedBody };
    }

    if (response.status === 500) {
      return {
        kind: "serverError",
        detail:
          typeof detail === "string"
            ? detail
            : "The RAG pipeline failed to answer the question.",
      };
    }

    return {
      kind: "networkError",
      message: `Unexpected response from the backend (status ${response.status}).`,
    };
  } catch (error) {
    if (timedOut) {
      return { kind: "timeout" };
    }

    const message =
      error instanceof Error
        ? error.message
        : "Unable to reach the backend.";

    return { kind: "networkError", message };
  } finally {
    clearTimeout(timeoutId);
  }
}

export { API_BASE_URL };
export const DEFAULT_CHAT_TIMEOUT_MS = 20_000;
export const DEFAULT_HEALTH_TIMEOUT_MS = 5_000;
