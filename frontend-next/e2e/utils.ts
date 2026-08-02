import { expect, type Page } from "@playwright/test";
import path from "node:path";

export const SHOTS_DIR =
  "/tmp/aegisrag-playwright-shots";

export function shotPath(name: string): string {
  return path.join(SHOTS_DIR, name);
}

/**
 * Waits for the composer to report the "online" state (real backend
 * health, not simulated) before interacting with it. `useHealthStatus`
 * fires its first check immediately on mount.
 */
export async function waitForBackendOnline(page: Page) {
  await expect(page.locator(".status-row").getByText("Backend online")).toBeVisible({
    timeout: 20_000,
  });
}

/** Submits a question by typing into the textarea and pressing Enter. */
export async function askQuestion(page: Page, question: string) {
  const textarea = page.locator(".composer textarea");
  await textarea.click();
  await textarea.fill(question);
  await textarea.press("Enter");
}

/**
 * Waits for the chat state machine to leave "submitting" for a real
 * backend round trip — resolves once one of success/noSources/error DOM
 * markers appears.
 */
export async function waitForResolution(page: Page, timeout = 45_000) {
  // NOTE: `.assistant-card` alone is not resolution-specific — the
  // "submitting" loading card also carries the `assistant-card` class
  // (`className="assistant-card loading-card"` in AnswerPanel), so a bare
  // `.assistant-card` selector matches immediately during submission, not
  // only after the real backend responds. `.answer-text` (rendered only
  // for success/noSources, once a real `answer` string exists) and
  // `.error-card` are the resolution-specific markers instead.
  await expect(
    page.locator(".answer-text, .error-card").first(),
  ).toBeVisible({ timeout });
}
