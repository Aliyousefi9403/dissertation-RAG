"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Database,
  History as HistoryIcon,
  Lock,
  Menu,
  MessageSquare,
  Settings as SettingsIcon,
  ShieldCheck,
  Swords,
  X,
} from "lucide-react";
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
  icon: typeof MessageSquare;
}

/**
 * Final navigation order for the sprint. Only Assistant and Knowledge Base
 * are routable today; the rest are visible-but-disabled placeholders for
 * future work. Icons are shown alongside the label at full width, and
 * alone (label hidden via CSS) in the <=1024px icons-only rail -- see
 * `.nav-label` in globals.css.
 */
const NAV_ITEMS: NavItem[] = [
  { label: "Assistant", href: "/", enabled: true, icon: MessageSquare },
  { label: "History", href: "/history", enabled: true, icon: HistoryIcon },
  { label: "Knowledge Base", href: "/knowledge-base", enabled: true, icon: Database },
  { label: "Attack Lab", href: "/attack-lab", enabled: false, icon: Swords },
  { label: "Defence Engine", href: "/defence-engine", enabled: false, icon: ShieldCheck },
  { label: "Analytics", href: "/analytics", enabled: false, icon: BarChart3 },
  { label: "Settings", href: "/settings", enabled: false, icon: SettingsIcon },
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
  // Only meaningful <=768px (see `.sidebar-toggle`/`.sidebar-backdrop` in
  // globals.css, hidden above that breakpoint) -- the sidebar becomes a
  // slide-in drawer rather than a fixed column at that width.
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  // Adjusting state during render (React's recommended alternative to a
  // setState-in-effect) to never leave the drawer open behind a route
  // change -- avoids the extra cascading-render effect would cause.
  const [previousPathname, setPreviousPathname] = useState(pathname);
  if (pathname !== previousPathname) {
    setPreviousPathname(pathname);
    setIsDrawerOpen(false);
  }

  useEffect(() => {
    if (!isDrawerOpen) {
      return;
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsDrawerOpen(false);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isDrawerOpen]);

  return (
    <>
      <button
        type="button"
        className="sidebar-toggle"
        aria-label={isDrawerOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={isDrawerOpen}
        aria-controls="app-sidebar"
        onClick={() => setIsDrawerOpen((open) => !open)}
      >
        {isDrawerOpen ? (
          <X aria-hidden="true" size={20} />
        ) : (
          <Menu aria-hidden="true" size={20} />
        )}
      </button>

      {isDrawerOpen && (
        <div
          className="sidebar-backdrop"
          aria-hidden="true"
          onClick={() => setIsDrawerOpen(false)}
        />
      )}

      <aside id="app-sidebar" className={cn("sidebar", isDrawerOpen && "sidebar--open")}>
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
            const Icon = item.icon;

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
                        <Icon aria-hidden="true" size={16} className="nav-icon" />
                        <span className="nav-label">{item.label}</span>
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
                  <Icon aria-hidden="true" size={16} className="nav-icon" />
                  <span className="nav-label">{item.label}</span>
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
    </>
  );
}
