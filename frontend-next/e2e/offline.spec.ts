import { test, expect } from "@playwright/test";
import { shotPath } from "./utils";

test.describe("Offline state (simulated via /health route interception)", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("composer disables and UI communicates offline without a false processing animation", async ({
    page,
  }) => {
    // Fail every /health request the app makes (matches useHealthStatus's
    // getHealth() -> request({ path: "/health" }) call), regardless of
    // API base host/port.
    await page.route("**/health", (route) => route.abort("failed"));

    await page.goto("/");

    await expect(page.locator(".status-row")).toContainText("Backend unavailable", {
      timeout: 20_000,
    });

    // Composer textarea is disabled and its placeholder communicates the
    // offline/reconnecting state.
    const textarea = page.locator(".composer textarea");
    await expect(textarea).toBeDisabled();
    await expect(textarea).toHaveAttribute(
      "placeholder",
      /offline|reconnect/i,
    );

    // The composer form's data-state must be "disabled", never
    // "submitting" — no false "processing" animation while offline.
    await expect(page.locator("form.composer")).toHaveAttribute("data-state", "disabled");

    // Submit button also disabled (nothing to submit / can't submit).
    await expect(page.getByRole("button", { name: "Send question" })).toBeDisabled();

    // The living-core layer must reflect "dormant", not any active/
    // submitting visual — assert via whichever presentation is active.
    const captionOrFallback = page.locator(
      ".living-core-status-caption, .living-core-fallback-text p",
    );
    await expect(captionOrFallback.first()).toContainText(/offline/i);

    await page.screenshot({ path: shotPath("offline-idle.png"), fullPage: true });
  });
});
