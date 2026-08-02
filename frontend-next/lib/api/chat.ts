import { DEFAULT_CHAT_TIMEOUT_MS, request, type ApiResult } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "@/lib/types/chat";

export async function postChat(
  question: string,
): Promise<ApiResult<ChatResponse>> {
  const payload: ChatRequest = { question };

  return request<ChatResponse>({
    method: "POST",
    path: "/chat",
    body: payload,
    timeoutMs: DEFAULT_CHAT_TIMEOUT_MS,
  });
}
