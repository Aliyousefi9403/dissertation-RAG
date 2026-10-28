/** Types mirroring the backend `/health` contract exactly. */

export interface HealthResponse {
  status: string;
}

export type HealthStatus = "checking" | "online" | "offline";
