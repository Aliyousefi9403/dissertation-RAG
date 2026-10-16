import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";

import "./globals.css";

import { DotFieldBackdrop } from "@/components/backdrop/DotFieldBackdrop";
import { AppSidebar } from "@/components/nav/AppSidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SmoothScrollProvider } from "@/components/smooth-scroll-provider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "AegisRAG",
  description:
    "A knowledge integrity research platform for secure retrieval-augmented generation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${GeistSans.variable} ${GeistMono.variable}`}
    >
      <body className="min-h-full">
        <SmoothScrollProvider>
          {/* Page-layout-root ambient backdrop — deliberately mounted above
              `{children}` in source order but pinned behind everything via
              `z-index: -1` in `.dot-field-canvas` (see globals.css), so it
              never depends on `app/page.tsx`'s own stacking. A separate,
              lightweight 2D canvas from `LivingCoreStage`'s r3f canvas — see
              `components/backdrop/DotFieldBackdrop.tsx`. */}
          <DotFieldBackdrop />
          {/* `.app-shell` (sidebar + per-route workspace) now lives here so
              every route shares one `AppSidebar` instance instead of each
              page re-declaring its own — see `components/nav/AppSidebar.tsx`
              and the `.app-shell`/`.sidebar` rules in globals.css, which are
              unchanged, only relocated to this file. */}
          <TooltipProvider>
            <main className="app-shell">
              <AppSidebar />
              {children}
            </main>
          </TooltipProvider>
        </SmoothScrollProvider>
      </body>
    </html>
  );
}