#!/bin/bash
# Builds main.pdf and the arXiv upload bundle (arxiv-upload.tar.gz: main.tex, main.bbl, refs.bib, figures/).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p figures
cp ../../research/figures/fig6_detector_robustness.png ../../research/figures/fig7_attacker_budget.png figures/
latexmk -pdf -interaction=nonstopmode -quiet main.tex
tar czf arxiv-upload.tar.gz main.tex main.bbl refs.bib figures
echo built
