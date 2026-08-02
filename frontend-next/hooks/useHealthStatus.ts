"use client";

import { useEffect, useRef, useState } from "react";

import { getHealth } from "@/lib/api/health";
import type { HealthStatus } from "@/lib/types/health";

const POLL_INTERVAL_MS = 15_000;

export function useHealthStatus(): HealthStatus {
  const [status, setStatus] = useState<HealthStatus>("checking");
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    async function checkHealth() {
      const result = await getHealth();

      if (!isMountedRef.current) {
        return;
      }

      setStatus(result.kind === "ok" ? "online" : "offline");
    }

    void checkHealth();

    const intervalId = setInterval(() => {
      if (document.visibilityState === "visible") {
        void checkHealth();
      }
    }, POLL_INTERVAL_MS);

    return () => {
      isMountedRef.current = false;
      clearInterval(intervalId);
    };
  }, []);

  return status;
}
