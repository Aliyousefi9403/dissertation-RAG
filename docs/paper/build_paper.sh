#!/bin/bash
# Builds the paper from aegisrag-paper.md: an editable Word file (native equations) and a PDF
# (HTML with MathML, printed by Chromium). Run: bash docs/paper/build_paper.sh
set -euo pipefail
cd "$(dirname "$0")"
pandoc aegisrag-paper.md --resource-path=.:../research/figures -o aegisrag-paper.docx
python3 style_docx.py aegisrag-paper.docx
pandoc aegisrag-paper.md --standalone --mathml --embed-resources --resource-path=.:../research/figures \
  --css paper.css --metadata pagetitle="AegisRAG paper" -o aegisrag-paper.html
node print_pdf.cjs
rm -f aegisrag-paper.html
echo "built aegisrag-paper.docx and aegisrag-paper.pdf"
