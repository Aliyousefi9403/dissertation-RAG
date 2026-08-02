import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the AegisRAG frontend UI verification suite.
 *
 * Both the backend (http://127.0.0.1:8000) and the Next.js dev server
 * (http://localhost:3000) are assumed to already be running — this suite
 * intentionally does NOT start or manage either process (`webServer` is
 * left unset) so it never touches the real, already-running backend.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 15_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
