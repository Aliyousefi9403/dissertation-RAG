import { DEFAULT_CHAT_TIMEOUT_MS, request, type ApiResult } from "@/lib/api/client";
import type { ChatRequest, ChatResponse, SystemState } from "@/lib/types/chat";

export async function postChat(
  question: string,
  systemState: SystemState = "clean",
): Promise<ApiResult<ChatResponse>> {
  const payload: ChatRequest = { question, system_state: systemState };

  return request<ChatResponse>({
    method: "POST",
    path: "/chat",
    body: payload,
    timeoutMs: DEFAULT_CHAT_TIMEOUT_MS,
  });
}
