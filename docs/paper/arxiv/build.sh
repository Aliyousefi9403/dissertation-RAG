#!/bin/bash
# Builds main.pdf and the arXiv upload bundle (arxiv-upload.tar.gz: main.tex, main.bbl, refs.bib; all figures are drawn in LaTeX).
set -euo pipefail
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode -quiet main.tex
tar czf arxiv-upload.tar.gz main.tex main.bbl refs.bib
echo built
