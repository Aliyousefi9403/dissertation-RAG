import { request, type ApiResult } from "@/lib/api/client";
import type {
  ExperimentRecord,
  ExperimentStats,
  HistoryFilters,
} from "@/lib/types/history";

function buildQuery(filters: HistoryFilters = {}): string {
  const params = new URLSearchParams();

  if (filters.mode) params.set("mode", filters.mode);
  if (filters.attack_method) params.set("attack_method", filters.attack_method);
  if (filters.answer_changed !== undefined) {
    params.set("answer_changed", String(filters.answer_changed));
  }
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));

  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function listHistory(
  filters?: HistoryFilters,
): Promise<ApiResult<ExperimentRecord[]>> {
  return request<ExperimentRecord[]>({
    method: "GET",
    path: `/history${buildQuery(filters)}`,
    timeoutMs: 10_000,
  });
}

export async function getHistoryEntry(
  id: number,
): Promise<ApiResult<ExperimentRecord>> {
  return request<ExperimentRecord>({
    method: "GET",
    path: `/history/${id}`,
    timeoutMs: 10_000,
  });
}

export async function getHistoryStats(): Promise<ApiResult<ExperimentStats>> {
  return request<ExperimentStats>({
    method: "GET",
    path: "/history/stats",
    timeoutMs: 10_000,
  });
}
