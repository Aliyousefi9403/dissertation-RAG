import { test, expect } from "@playwright/test";
import { askQuestion, shotPath, waitForResolution } from "./utils";

test.describe("Reduced motion", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("static DOM/CSS fallback renders instead of the WebGL canvas", async ({ page }) => {
    // `page.emulateMedia` must be called BEFORE the initial navigation:
    // `useReducedMotion()` (framer-motion) reads `matchMedia` on first
    // mount, and calling emulateMedia after `goto` does not reliably
    // retrofit that already-resolved value in this Playwright/Chromium
    // combination (confirmed via manual repro — see task report).
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");

    await expect(page.locator(".composer textarea")).toBeVisible({ timeout: 20_000 });

    // No WebGL canvas should be mounted under the living-core wrapper.
    await expect(page.locator(".living-core-canvas-wrap canvas")).toHaveCount(0);

    // The static, non-animating fallback is rendered instead.
    const fallback = page.locator(".living-core-fallback");
    await expect(fallback).toBeVisible();
    await expect(fallback).toHaveAttribute("role", "status");
    await expect(fallback).toHaveAttribute("aria-live", "polite");

    await page.screenshot({ path: shotPath("reduced-motion-idle.png"), fullPage: true });
  });

  test("real state info (status text, source count) still present after submit", async ({
    page,
  }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    await expect(page.locator(".composer textarea")).toBeEnabled({ timeout: 20_000 });

    await askQuestion(page, "What is a buffer overflow attack?");
    await waitForResolution(page);

    // No canvas should ever appear, even post-submit.
    await expect(page.locator(".living-core-canvas-wrap canvas")).toHaveCount(0);

    const fallbackText = await page.locator(".living-core-fallback-text p").innerText();
    expect(fallbackText.length).toBeGreaterThan(0);

    const hasEvidence = (await page.locator(".evidence-section").count()) > 0;
    if (hasEvidence) {
      const rowCount = await page.locator(".source-row").count();
      expect(fallbackText).toContain(String(rowCount));
      // Static fallback should also list every real source by number.
      await expect(page.locator(".living-core-source-item")).toHaveCount(rowCount);
    } else {
      await expect(page.locator(".no-sources-card")).toBeVisible();
    }

    await page.screenshot({
      path: shotPath("reduced-motion-resolved.png"),
      fullPage: true,
    });
  });
});
