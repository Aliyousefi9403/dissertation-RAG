// Prints runtime-monitor-report.html to runtime-monitor-report.pdf with the installed Chromium (MathML equations render natively).
const path = require("path");
const { chromium } = require(path.resolve(__dirname, "../../frontend-next/node_modules/@playwright/test"));
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium" });
  const page = await browser.newPage();
  await page.goto("file://" + path.resolve(__dirname, "runtime-monitor-report.html"), { waitUntil: "load" });
  await page.pdf({ path: path.resolve(__dirname, "runtime-monitor-report.pdf"), format: "A4", printBackground: true,
    displayHeaderFooter: true, headerTemplate: "<span></span>",
    footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#666"><span class="pageNumber"></span></div>',
    margin: { top: "18mm", bottom: "18mm", left: "18mm", right: "18mm" } });
  await browser.close();
})();
