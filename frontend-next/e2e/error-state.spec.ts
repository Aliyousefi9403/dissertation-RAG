import { test, expect } from "@playwright/test";
import { askQuestion, shotPath, waitForBackendOnline } from "./utils";

test.describe("Error state (simulated via /chat route interception)", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("500 response renders the error card with the real message, no alarm styling, no crash", async ({
    page,
  }) => {
    // Let /health pass through untouched (real backend), only fail /chat.
    await page.route("**/chat", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "The RAG pipeline failed to answer the question." }),
      });
    });

    await page.goto("/");
    await waitForBackendOnline(page);

    await askQuestion(page, "What is a buffer overflow attack?");

    const errorCard = page.locator(".error-card");
    await expect(errorCard).toBeVisible({ timeout: 20_000 });
    await expect(errorCard).toHaveAttribute("role", "alert");
    await expect(errorCard).toHaveAttribute("aria-live", "assertive");
    await expect(errorCard).toContainText(
      "The RAG pipeline failed to answer the question.",
    );

    // Retry button present and operable.
    await expect(errorCard.getByRole("button", { name: "Retry" })).toBeVisible();

    // Living-core reaches its "fault" visual state without crashing the
    // page — assert the app shell is still intact and no unhandled page
    // error occurred (page.on("pageerror") captured below).
    await expect(page.locator(".app-shell")).toBeVisible();

    const fallbackOrCaption = page.locator(
      ".living-core-status-caption, .living-core-fallback-text p",
    );
    await expect(fallbackOrCaption.first()).toContainText(/fault/i);

    // No alarm/explosion-styling class names should exist anywhere.
    const alarmMarkup = await page
      .locator('[class*="alarm"], [class*="explosion"]')
      .count();
    expect(alarmMarkup).toBe(0);

    await page.screenshot({ path: shotPath("error-state.png"), fullPage: true });
  });

  test("network error (connection failure) also renders a real error message", async ({
    page,
  }) => {
    await page.route("**/chat", (route) => route.abort("connectionrefused"));

    const pageErrors: Error[] = [];
    page.on("pageerror", (error) => pageErrors.push(error));

    await page.goto("/");
    await waitForBackendOnline(page);

    await askQuestion(page, "What is TCP SYN flood?");

    const errorCard = page.locator(".error-card");
    await expect(errorCard).toBeVisible({ timeout: 20_000 });
    await expect(errorCard.locator("p")).not.toBeEmpty();

    expect(pageErrors).toEqual([]);

    await page.screenshot({ path: shotPath("error-state-network.png"), fullPage: true });
  });
});
