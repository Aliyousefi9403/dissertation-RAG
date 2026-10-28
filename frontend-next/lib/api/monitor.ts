import { request, type ApiResult } from "@/lib/api/client";
import type { MonitorMemory } from "@/lib/types/monitor";

export function getMonitorMemory(): Promise<ApiResult<MonitorMemory>> {
  return request<MonitorMemory>({ method: "GET", path: "/monitor/memory", timeoutMs: 10_000 });
}

/** Starts a fresh memory; the backend archives the old file rather than deleting it. */
export function resetMonitorMemory(): Promise<
  ApiResult<{ archived: string | null; count: number }>
> {
  return request({ method: "POST", path: "/monitor/memory/reset", body: {}, timeoutMs: 10_000 });
}
