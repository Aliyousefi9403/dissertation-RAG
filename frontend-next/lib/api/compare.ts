import { request, type ApiResult } from "@/lib/api/client";
import type { CompareRequest, CompareResponse } from "@/lib/types/compare";

/** `/compare` runs the clean and PWWS-poisoned pipelines back to back, so
 * it gets a longer budget than the single `/chat` call. */
const COMPARE_TIMEOUT_MS = 40_000;

export async function postCompare(
  question: string,
): Promise<ApiResult<CompareResponse>> {
  const payload: CompareRequest = { question };

  return request<CompareResponse>({
    method: "POST",
    path: "/compare",
    body: payload,
    timeoutMs: COMPARE_TIMEOUT_MS,
  });
}
