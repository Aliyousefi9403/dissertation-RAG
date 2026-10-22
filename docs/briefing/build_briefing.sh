#!/bin/bash
# Builds the project briefing as an editable Word file and a PDF (needs pandoc and Chromium).
set -euo pipefail
cd "$(dirname "$0")"
pandoc aegisrag-project-briefing.md -o aegisrag-project-briefing.docx
python3 ../paper/style_docx.py aegisrag-project-briefing.docx
pandoc aegisrag-project-briefing.md --standalone --embed-resources --css ../paper/paper.css \
  --metadata pagetitle="AegisRAG briefing" -o aegisrag-project-briefing.html
node -e '
const path = require("path");
const { chromium } = require(path.resolve("../../frontend-next/node_modules/@playwright/test"));
(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const p = await b.newPage();
  await p.goto("file://" + path.resolve("aegisrag-project-briefing.html"));
  await p.pdf({ path: "aegisrag-project-briefing.pdf", format: "A4", printBackground: true, displayHeaderFooter: true,
    headerTemplate: "<span></span>", footerTemplate: "<div style=\"font-size:8px;width:100%;text-align:center;color:#666\"><span class=\"pageNumber\"></span></div>",
    margin: { top: "18mm", bottom: "18mm", left: "18mm", right: "18mm" } });
  await b.close();
})();'
rm -f aegisrag-project-briefing.html
echo built
