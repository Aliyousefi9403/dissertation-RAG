"""Gantt chart for the PDD work plan (docs/pdd/gantt.png). Run: python3 make_gantt.py"""
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

BLUE, MUTED, INK, GRID = "#2a78d6", "#5f5e5a", "#0b0b0b", "#e4e3df"
ACTIVITIES = [
    ("A1 Literature review, threat model", date(2026, 10, 1), date(2026, 11, 8)),
    ("A2 RAG pipeline, interface, three corpora", date(2026, 10, 1), date(2026, 10, 31)),
    ("A3 Benchmark build, review, freeze", date(2026, 10, 15), date(2026, 11, 8)),
    ("A4 Pilot and first paired evaluation", date(2026, 11, 1), date(2026, 11, 22)),
    ("A5 Relative-entropy detectors (offline)", date(2026, 11, 9), date(2026, 12, 20)),
    ("A6 Live defences, judge check", date(2026, 12, 1), date(2027, 1, 31)),
    ("A7 Adaptive attackers, second attack", date(2027, 1, 4), date(2027, 2, 14)),
    ("A8 Evidence check, held-out and uncertainty analysis", date(2027, 2, 1), date(2027, 3, 7)),
    ("A9 Runtime verification monitor: design, build, evaluate", date(2027, 1, 18), date(2027, 3, 7)),
    ("A10 Report, demo video, paper, reproducibility", date(2027, 2, 1), date(2027, 4, 4)),
]
MILESTONES = [("PDD + ethics form", date(2026, 11, 11)), ("Final submission", date(2027, 4, 4))]

fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
for k, (label, start, end) in enumerate(ACTIVITIES):
    ax.barh(k, mdates.date2num(end) - mdates.date2num(start), left=mdates.date2num(start), height=0.55, color=BLUE)
ax.set_yticks(range(len(ACTIVITIES)), [a[0] for a in ACTIVITIES], fontsize=7)
ax.invert_yaxis()
for label, day in MILESTONES:
    ax.axvline(mdates.date2num(day), color=MUTED, lw=1, ls="--")
    right = day.month == 4
    ax.text(mdates.date2num(day) + (-3 if right else 3), -0.9, label, fontsize=6.5, color=MUTED, ha="right" if right else "left")
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
ax.tick_params(axis="x", labelsize=7)
ax.set_xlim(mdates.date2num(date(2026, 9, 28)), mdates.date2num(date(2027, 4, 12)))
ax.set_ylim(len(ACTIVITIES) - 0.4, -1.3)
ax.grid(axis="x", color=GRID, lw=0.6)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
fig.tight_layout()
fig.savefig("gantt.png")
