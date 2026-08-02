"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Lock } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils";
import { useHealthStatus } from "@/hooks/useHealthStatus";
import { StatusBar } from "@/components/StatusBar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NavItem {
  label: string;
  href: string;
  enabled: boolean;
}

/**
 * Final navigation order for the sprint. Only Assistant and Knowledge Base
 * are routable today; the rest are visible-but-disabled placeholders for
 * future work.
 */
const NAV_ITEMS: NavItem[] = [
  { label: "Assistant", href: "/", enabled: true },
  { label: "Knowledge Base", href: "/knowledge-base", enabled: true },
  { label: "Attack Lab", href: "/attack-lab", enabled: false },
  { label: "Defence Engine", href: "/defence-engine", enabled: false },
  { label: "Analytics", href: "/analytics", enabled: false },
  { label: "Settings", href: "/settings", enabled: false },
];

/**
 * Shared app sidebar (brand, primary navigation, backend status). Lifted
 * out of `app/page.tsx` so it can be mounted once in `app/layout.tsx` and
 * shared across every real route (`/`, `/knowledge-base`, …) instead of
 * being duplicated per page.
 */
export function AppSidebar() {
  const pathname = usePathname();
  const healthStatus = useHealthStatus();
  const prefersReducedMotion = useReducedMotion();

  return (
    <aside className="sidebar">
      <div className="brand">
        <Image
          src="/aegisrag-logo.png"
          alt="AegisRAG logo"
          width={58}
          height={58}
          priority
        />

        <div>
          <h1>AegisRAG</h1>
          <p>Knowledge integrity platform</p>
        </div>
      </div>

      <nav className="navigation" aria-label="Main navigation">
        {NAV_ITEMS.map((item) => {
          if (!item.enabled) {
            return (
              <Tooltip key={item.label}>
                <TooltipTrigger
                  render={
                    <span
                      className="nav-item"
                      aria-disabled="true"
                      tabIndex={-1}
                    >
                      <span>{item.label}</span>
                      <Lock aria-hidden="true" size={13} className="nav-lock-icon" />
                    </span>
                  }
                />
                <TooltipContent side="right">Coming soon</TooltipContent>
              </Tooltip>
            );
          }

          const isActive = pathname === item.href;

          return (
            <motion.div
              key={item.label}
              whileHover={prefersReducedMotion ? undefined : { x: 2 }}
              whileTap={prefersReducedMotion ? undefined : { scale: 0.98 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
            >
              <Link
                href={item.href}
                className={cn("nav-item", isActive && "active")}
                aria-current={isActive ? "page" : undefined}
              >
                <span>{item.label}</span>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <StatusBar healthStatus={healthStatus} />
        <p>AegisRAG v0.1.0</p>
      </div>
    </aside>
  );
}
