import { DEFAULT_CHAT_TIMEOUT_MS, request, type ApiResult } from "@/lib/api/client";
import type { ChatRequest, ChatResponse, SystemState } from "@/lib/types/chat";

/** Verified mode may regenerate up to twice and load the trusted reference; Contextual mode loads a
 * language model on its first question. Both need longer than a plain answer. */
const SLOW_TIMEOUT_MS = 90_000;
const SLOW_STATES: SystemState[] = ["verified", "contextual"];

export async function postChat(
  question: string,
  systemState: SystemState = "clean",
  options: { trustedFallback?: boolean } = {},
): Promise<ApiResult<ChatResponse>> {
  const payload: ChatRequest = { question, system_state: systemState };
  if (systemState === "verified" && options.trustedFallback) {
    payload.trusted_fallback = true;
  }

  return request<ChatResponse>({
    method: "POST",
    path: "/chat",
    body: payload,
    timeoutMs: SLOW_STATES.includes(systemState) ? SLOW_TIMEOUT_MS : DEFAULT_CHAT_TIMEOUT_MS,
  });
}
