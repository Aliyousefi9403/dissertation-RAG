#!/bin/bash
# Builds the paper from aegisrag-paper.md: an editable Word file and a PDF.
# Run from anywhere: bash docs/paper/build_paper.sh   (needs pandoc and LibreOffice)
set -euo pipefail
cd "$(dirname "$0")"
pandoc aegisrag-paper.md --resource-path=.:../research/figures -o aegisrag-paper.docx
python3 style_docx.py aegisrag-paper.docx
soffice --headless --convert-to pdf aegisrag-paper.docx >/dev/null 2>&1
echo "built aegisrag-paper.docx and aegisrag-paper.pdf"
