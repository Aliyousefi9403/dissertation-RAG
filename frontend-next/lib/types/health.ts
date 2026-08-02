/**
 * Types mirroring the backend `/health` contract exactly.
 * See backend/app/main.py.
 */

export interface HealthResponse {
  status: string;
}

export type HealthStatus = "checking" | "online" | "offline";
