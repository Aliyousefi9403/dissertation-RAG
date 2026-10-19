import { test, expect, type Page } from "@playwright/test";
import { askQuestion, shotPath, waitForResolution } from "./utils";

const VIEWPORTS = [
  { name: "tablet", width: 820, height: 1180 },
  { name: "mobile", width: 390, height: 844 },
];

async function assertNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return {
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
    };
  });
  // Allow a 1px rounding tolerance.
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 1);
}

for (const viewport of VIEWPORTS) {
  test.describe(`${viewport.name} (${viewport.width}x${viewport.height})`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test(`idle state adapts sidebar and has no horizontal clipping`, async ({ page }) => {
      await page.goto("/");
      await expect(page.locator(".composer textarea")).toBeVisible({ timeout: 20_000 });

      // Sidebar per globals.css: <=1024px an icons-only rail (60px);
      // <=768px a slide-in drawer, translated off-screen until the toggle
      // opens it (Playwright counts a translated element as visible, so
      // check its box rather than visibility).
      const sidebar = page.locator(".sidebar");
      await expect(sidebar).toBeAttached();
      const box = await sidebar.boundingBox();
      expect(box).not.toBeNull();
      if (viewport.width > 768) {
        await expect(sidebar).toBeVisible();
        expect(box!.width).toBeLessThanOrEqual(64);
      } else {
        expect(box!.x + box!.width).toBeLessThanOrEqual(1);
        await expect(page.locator(".sidebar-toggle")).toBeVisible();
      }

      await assertNoHorizontalOverflow(page);

      await page.screenshot({
        path: shotPath(`${viewport.name}-idle.png`),
        fullPage: true,
      });
    });

    test(`submit flow has no clipping and resolves`, async ({ page }) => {
      await page.goto("/");
      await expect(page.locator(".composer textarea")).toBeEnabled({ timeout: 20_000 });

      await askQuestion(page, "What is a buffer overflow attack?");
      await expect(page.locator(".loading-card")).toBeVisible();

      await assertNoHorizontalOverflow(page);
      await page.screenshot({
        path: shotPath(`${viewport.name}-submitting.png`),
        fullPage: true,
      });

      await waitForResolution(page);
      await assertNoHorizontalOverflow(page);

      // Confirm the response stack's bounding box stays within the
      // viewport width (no element escaping the layout).
      const box = await page.locator(".response-stack").boundingBox();
      expect(box).not.toBeNull();
      if (box) {
        expect(box.x).toBeGreaterThanOrEqual(0);
        expect(box.x + box.width).toBeLessThanOrEqual(viewport.width + 1);
      }

      await page.screenshot({
        path: shotPath(`${viewport.name}-resolved.png`),
        fullPage: true,
      });
    });
  });
}
