import { DEFAULT_HEALTH_TIMEOUT_MS, request, type ApiResult } from "@/lib/api/client";
import type { HealthResponse } from "@/lib/types/health";

export async function getHealth(): Promise<ApiResult<HealthResponse>> {
  return request<HealthResponse>({
    method: "GET",
    path: "/health",
    timeoutMs: DEFAULT_HEALTH_TIMEOUT_MS,
  });
}
