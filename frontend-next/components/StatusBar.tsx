import { cn } from "@/lib/utils";
import type { HealthStatus } from "@/lib/types/health";

interface StatusBarProps {
  healthStatus: HealthStatus;
}

const STATUS_COPY: Record<HealthStatus, string> = {
  checking: "Checking backend…",
  online: "Backend online",
  offline: "Backend unavailable",
};

export function StatusBar({ healthStatus }: StatusBarProps) {
  return (
    <div className="status-row" role="status">
      <span
        aria-hidden="true"
        className={cn(
          "status-dot",
          healthStatus === "online" && "status-dot--online",
          healthStatus === "offline" && "status-dot--offline",
          healthStatus === "checking" && "status-dot--checking",
        )}
      />
      <span>{STATUS_COPY[healthStatus]}</span>
    </div>
  );
}
