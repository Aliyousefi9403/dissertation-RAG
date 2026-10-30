#!/bin/bash
# Builds runtime-monitor-report.pdf from runtime-monitor-report.md (HTML with MathML, printed by Chromium).
set -euo pipefail
cd "$(dirname "$0")"
pandoc runtime-monitor-report.md --standalone --mathml --embed-resources --css ../paper/paper.css \
  --metadata pagetitle="AegisRAG runtime monitor" -o runtime-monitor-report.html
node print_report.cjs
rm -f runtime-monitor-report.html
echo built runtime-monitor-report.pdf
