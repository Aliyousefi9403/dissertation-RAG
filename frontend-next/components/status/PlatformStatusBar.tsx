"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import {
  getPlatformStatus,
  type PlatformStatus,
} from "@/lib/mock/platformStatus";

/**
 * Top-of-workspace platform status bar — Trust Score, Knowledge Base
 * Health, Documents Indexed, Active LLM and Security Status.
 *
 * Distinct from `components/StatusBar.tsx` (the existing sidebar-footer
 * backend online/offline dot indicator) — this is a separate, wider
 * summary strip for the Assistant workspace, backed by
 * `lib/mock/platformStatus.ts` (mock pending a real endpoint).
 */
export function PlatformStatusBar() {
  const [status, setStatus] = useState<PlatformStatus | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getPlatformStatus()
      .then((result) => {
        if (!cancelled) {
          setStatus(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) {
    return (
      <div className="platform-status-bar platform-status-bar--error" role="status">
        <ShieldAlert aria-hidden="true" size={15} />
        <span>Platform status is temporarily unavailable.</span>
      </div>
    );
  }

  if (!status) {
    return (
      <div
        className="platform-status-bar"
        aria-busy="true"
        aria-label="Loading platform status"
      >
        {Array.from({ length: 5 }).map((_, index) => (
          <div className="platform-status-item" key={index}>
            <Skeleton className="platform-status-skeleton-label" />
            <Skeleton className="platform-status-skeleton-value" />
          </div>
        ))}
      </div>
    );
  }

  const isHealthy = status.knowledgeBaseHealth === "Healthy";
  const isSecure = status.securityStatus === "Nominal";

  return (
    <div className="platform-status-bar" role="status">
      <div className="platform-status-item">
        <span className="platform-status-label">Trust score</span>
        <span className="platform-status-value platform-status-value--accent">
          {status.trustScorePercent}%
        </span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Knowledge base</span>
        <span
          className={
            isHealthy
              ? "platform-status-value platform-status-value--ok"
              : "platform-status-value platform-status-value--warn"
          }
        >
          {status.knowledgeBaseHealth}
        </span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Documents indexed</span>
        <span className="platform-status-value">
          {status.documentsIndexed.toLocaleString()}
        </span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Active LLM</span>
        <span className="platform-status-value" title={status.activeLlm}>
          {status.activeLlm}
        </span>
      </div>

      <div className="platform-status-item">
        <span className="platform-status-label">Security</span>
        <span className="platform-status-value platform-status-value--icon">
          {isSecure ? (
            <ShieldCheck aria-hidden="true" size={14} />
          ) : (
            <ShieldAlert aria-hidden="true" size={14} />
          )}
          {status.securityStatus}
        </span>
      </div>
    </div>
  );
}
