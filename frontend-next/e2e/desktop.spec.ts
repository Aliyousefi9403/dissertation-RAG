import { test, expect } from "@playwright/test";
import { askQuestion, shotPath, waitForBackendOnline, waitForResolution } from "./utils";

test.describe("Desktop (1440x900)", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("idle state renders living core, composer and online status", async ({ page }) => {
    await page.goto("/");
    await waitForBackendOnline(page);

    // Living core hero slot present (a layout slot: the core itself is drawn
    // by the fixed canvas frame, checked as canvas-or-fallback below).
    await expect(page.locator(".living-core-stage--hero")).toBeAttached();
    await expect(page.locator(".living-core-slot")).toBeAttached(); // zero-height marker (globals.css)

    // Either the real 3D canvas or the static DOM/CSS fallback must be
    // present (never neither) — whichever WebGL resolves to in this
    // headless browser. The dynamic `import()` of LivingCoreScene can take
    // a beat, so poll rather than doing a one-shot count.
    await expect(
      page.locator(".living-core-canvas-wrap canvas, .living-core-fallback"),
    ).toBeVisible({ timeout: 10_000 });

    // Composer visible and enabled (backend online, no request in flight).
    const textarea = page.locator(".composer textarea");
    await expect(textarea).toBeVisible();
    await expect(textarea).toBeEnabled();

    // Status bar shows "Backend online".
    await expect(page.locator(".status-row")).toContainText("Backend online");

    await page.screenshot({ path: shotPath("desktop-idle.png"), fullPage: true });
  });

  test("submitting a real question yields internally-consistent success or no-sources state", async ({
    page,
  }) => {
    await page.goto("/");
    await waitForBackendOnline(page);

    await askQuestion(page, "What is a buffer overflow attack?");

    // Submitting state: user question echoed, loading card visible, no
    // premature source/answer content.
    await expect(page.locator(".user-card")).toContainText(
      "What is a buffer overflow attack?",
    );
    await expect(page.locator(".loading-card")).toBeVisible();
    await page.screenshot({ path: shotPath("desktop-submitting.png"), fullPage: true });

    await waitForResolution(page);

    const responseStack = page.locator(".response-stack");
    await expect(responseStack).toBeVisible();

    const hasEvidenceSection = await page.locator(".evidence-section").count();
    const hasNoSourcesCard = await page.locator(".no-sources-card").count();
    const hasErrorCard = await page.locator(".error-card").count();

    expect(hasErrorCard).toBe(0); // Real backend is healthy; this should not error.
    expect(hasEvidenceSection + hasNoSourcesCard).toBeGreaterThan(0);

    if (hasEvidenceSection > 0) {
      // Assert internal consistency: the "N sources" count label matches
      // the actual number of rendered .source-row items.
      const countLabel = await page
        .locator(".evidence-section .section-heading span")
        .last()
        .innerText();
      const declaredCount = parseInt(countLabel, 10);
      const rowCount = await page.locator(".source-row").count();
      expect(rowCount).toBe(declaredCount);
      expect(rowCount).toBeGreaterThan(0);

      // The living-core status caption (or static fallback text) should
      // also mention the same source count.
      const caption = await page
        .locator(".living-core-status-caption, .living-core-fallback-text p")
        .first()
        .innerText();
      expect(caption).toContain(String(rowCount));
    } else {
      await expect(page.locator(".no-sources-card")).toContainText(
        "No relevant sources were found",
      );
    }

    await expect(page.locator(".assistant-card .answer-text")).toBeVisible();

    await page.screenshot({ path: shotPath("desktop-resolved.png"), fullPage: true });
  });

  test("Shift+Enter inserts a newline instead of submitting", async ({ page }) => {
    await page.goto("/");
    await waitForBackendOnline(page);

    const textarea = page.locator(".composer textarea");
    await textarea.click();
    await textarea.type("line one");
    await textarea.press("Shift+Enter");
    await textarea.type("line two");

    const value = await textarea.inputValue();
    expect(value).toBe("line one\nline two");

    // Still idle — no submission happened.
    await expect(page.locator(".idle-hint")).toBeVisible();
    await expect(page.locator(".user-card")).toHaveCount(0);
  });

  test("Enter alone submits the question", async ({ page }) => {
    await page.goto("/");
    await waitForBackendOnline(page);

    const textarea = page.locator(".composer textarea");
    await textarea.click();
    await textarea.type("What is TCP SYN flood?");
    await textarea.press("Enter");

    // Textarea clears and the question moves into the response stack.
    await expect(textarea).toHaveValue("");
    await expect(page.locator(".user-card")).toContainText("What is TCP SYN flood?");
  });
});
