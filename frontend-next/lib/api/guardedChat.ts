import { request, type ApiResult } from "@/lib/api/client";
import type { SystemState } from "@/lib/types/chat";
import type { GuardedChatRequest, GuardedChatResponse } from "@/lib/types/guardedChat";

/** A guarded request makes two bounded model calls (draft + verifier, each
 * with a server-side timeout and one retry), so it gets a longer client
 * budget than plain `/chat`. */
export const GUARDED_CHAT_TIMEOUT_MS = 180_000;

export async function postGuardedChat(
  question: string,
  systemState: SystemState = "clean",
): Promise<ApiResult<GuardedChatResponse>> {
  const payload: GuardedChatRequest = { question, system_state: systemState };

  return request<GuardedChatResponse>({
    method: "POST",
    path: "/guarded-chat",
    body: payload,
    timeoutMs: GUARDED_CHAT_TIMEOUT_MS,
  });
}
