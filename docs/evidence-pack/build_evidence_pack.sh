#!/bin/bash
# Builds evidence-pack.pdf and the shareable zip AegisRAG-evidence-pack.zip (needs pandoc, Chromium, Playwright).
set -euo pipefail
cd "$(dirname "$0")"
TMP=$(mktemp -d)
pandoc evidence-pack.md --standalone --embed-resources --resource-path=. --css ../paper/paper.css --metadata pagetitle="Evidence pack" -o "$TMP/ep.html"
node -e '
const { chromium } = require(require("path").resolve("../../frontend-next/node_modules/@playwright/test"));
(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const p = await b.newPage();
  await p.goto("file://" + process.argv[1]);
  await p.addStyleTag({content:"img{max-width:100%;max-height:115mm;display:block;margin:0 auto} table{font-size:9px} p:has(img){break-inside:avoid}"});
  await p.pdf({ path: "evidence-pack.pdf", format: "A4", printBackground: true, displayHeaderFooter: true,
    headerTemplate: "<span></span>", footerTemplate: "<div style=\"font-size:8px;width:100%;text-align:center;color:#666\"><span class=\"pageNumber\"></span></div>",
    margin: { top: "16mm", bottom: "16mm", left: "16mm", right: "16mm" } });
  await b.close();
})();' "$TMP/ep.html"
P="$TMP/AegisRAG-evidence-pack"; mkdir -p "$P/results" "$P/figures"
cp ../briefing/aegisrag-project-briefing.pdf "$P/01-briefing.pdf"
cp evidence-pack.pdf "$P/02-evidence-pack.pdf"
cp ../research/evaluation-methods-and-results.pdf "$P/03-results-write-up.pdf"
cp ../pdd/AegisRAG-Project-Definition-Document.pdf "$P/04-project-definition-document.pdf"
cp ../paper/aegisrag-paper.pdf "$P/05-paper-draft.pdf"
cp ../reports/AegisRAG-relative-entropy-report-for-Nikos.pdf "$P/06-note-for-dr-komninos.pdf"
cp ../demo/demo-video-plan.md "$P/07-demo-video-plan.md"
cp ../research/EVIDENCE.md "$P/results/EVIDENCE.md"
cp ../research/figures/*.png "$P/figures/"
(cd ../research/results && find . -name "summary.json" -o -name "*.json" -path "*detector*" -o -name "auroc-intervals.json" | while read f; do mkdir -p "$P/results/$(dirname "$f")"; cp "$f" "$P/results/$f"; done)
rm -f AegisRAG-evidence-pack.zip
(cd "$TMP" && zip -qr - AegisRAG-evidence-pack) > AegisRAG-evidence-pack.zip
rm -rf "$TMP"
echo built
