"""Figures for the relative-entropy detection report, from saved result files only.

Usage: python docs/research/scripts/make_figures.py   (writes docs/research/figures/*.png)
Palette: validated categorical slots (blue, orange, aqua, yellow); every bar is
direct-labelled because two slots are below 3:1 contrast on white.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "docs/research/results"
OUT = ROOT / "docs/research/figures"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#0b0b0b", "#5f5e5a", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})

SCORES = [("char_kl", "Letter-frequency KL\n(lecture example)"),
          ("kl_english", "Word KL vs\ngeneral English"),
          ("kl_domain", "Word KL vs\ndomain reference"),
          ("mean_domain", "Mean surprisal vs\ndomain reference"),
          ("syngap_top3_english", "Synonym gap vs\ngeneral English"),
          ("syngap_top3_domain", "Synonym gap vs\ndomain reference")]


def auroc_figure():
    poisoned = json.loads((RESULTS / "entropy-detector-20261016/detector-poisoned.json").read_text())["results"]["all"]
    control = json.loads((RESULTS / "entropy-detector-20261016/detector-control.json").read_text())["results"]["all"]
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=200)
    y = range(len(SCORES))
    h = 0.36
    for offset, data, color, label in ((-h / 2, poisoned, BLUE, "Poisoned corpus (real substitutions)"),
                                       (h / 2, control, ORANGE, "Control corpus (same sections, no substitutions)")):
        vals = [data[key]["auroc"] for key, _ in SCORES]
        bars = ax.barh([i + offset for i in y], vals, height=h - 0.04, color=color, label=label)
        for bar, v in zip(bars, vals):
            ax.text(v + 0.01, bar.get_y() + bar.get_height() / 2, f"{v:.2f}", va="center", fontsize=8, color=INK)
    ax.axvline(0.5, color=MUTED, lw=1, ls="--")
    ax.text(0.505, -0.62, "chance = 0.5", color=MUTED, fontsize=7.5, ha="left", va="bottom")
    ax.set_yticks(list(y), [label for _, label in SCORES])
    ax.set_xlim(0, 1)
    ax.set_xlabel("AUROC for finding chunks that contain PWWS-edited text (191 chunks, 47 edited)")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(len(SCORES) - 0.5, -0.75)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_auroc_poisoned_vs_control.png")
    plt.close(fig)


def roc_figure():
    rows = json.loads((RESULTS / "entropy-detector-20261016/detector-poisoned.json").read_text())["rows"]
    fig, ax = plt.subplots(figsize=(4.4, 4.0), dpi=200)
    for key, label, color in (("char_kl", "Letter-frequency KL", YELLOW), ("kl_english", "Word KL vs English", ORANGE),
                              ("kl_domain", "Word KL vs domain", AQUA), ("syngap_top3_domain", "Synonym gap vs domain", BLUE)):
        pts = sorted(((r[key], r["label"]) for r in rows), reverse=True)
        p = sum(lab for _, lab in pts)
        n = len(pts) - p
        tp = fp = 0
        xs, ys = [0.0], [0.0]
        for _, lab in pts:
            tp += lab
            fp += 1 - lab
            xs.append(fp / n)
            ys.append(tp / p)
        ax.plot(xs, ys, color=color, lw=2, label=label)
    ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--")
    ax.set_xlabel("False-positive rate (unedited chunks flagged)")
    ax.set_ylabel("True-positive rate (edited chunks flagged)")
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_roc_curves.png")
    plt.close(fig)


def defence_figure():
    path = RESULTS / "entropy-defence/live-paired/summary.json"
    if not path.exists():
        return
    s = json.loads(path.read_text())
    outcomes, pairs = s["outcomes"], s["pairs"]
    comp = s["comparisons"]
    conditions = [("clean", "Clean", BLUE), ("poisoned", "Poisoned", ORANGE),
                  ("defended", "Defended", AQUA), ("clean_filtered", "Clean\n+ filter", YELLOW)]
    exposure = {"clean": comp["defended_vs_clean"]["all"]["exposure"]["b"],
                "poisoned": comp["defended_vs_poisoned"]["all"]["exposure"]["b"],
                "defended": comp["defended_vs_poisoned"]["all"]["exposure"]["a"],
                "clean_filtered": comp["clean_filtered_vs_clean"]["all"]["exposure"]["a"]}
    correctness = {"clean": comp["defended_vs_clean"]["all"]["correctness"]["b"],
                   "poisoned": comp["defended_vs_poisoned"]["all"]["correctness"]["b"],
                   "defended": comp["defended_vs_poisoned"]["all"]["correctness"]["a"],
                   "clean_filtered": comp["clean_filtered_vs_clean"]["all"]["correctness"]["a"]}
    abstain = {c: outcomes[c]["abstained"] / pairs for c, _, _ in conditions}
    panels = [("Questions where edited text\nreached the model", exposure),
              ("Answer correctness\n(LLM judge, 0–1)", correctness),
              ("Answers that abstain\n(\"context does not say\")", abstain)]
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.0), dpi=200, sharey=False)
    for ax, (title, values) in zip(axes, panels):
        vals = [values[c] for c, _, _ in conditions]
        bars = ax.bar(range(4), vals, color=[col for _, _, col in conditions], width=0.72)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 0.015, f"{v:.2f}", ha="center", fontsize=7.5, color=INK)
        ax.set_title(title, fontsize=8.5, color=INK)
        ax.set_xticks(range(4), [lab for _, lab, _ in conditions], fontsize=7.5)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_defence_live.png")
    plt.close(fig)


def sweep_figure():
    path = RESULTS / "entropy-defence/threshold-sweep/sweep.json"
    if not path.exists():
        return
    s = json.loads(path.read_text())
    deployed = s["deployed_threshold_bits"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.6, 3.2), dpi=200, gridspec_kw={"width_ratios": [1.6, 1]})
    rows = sorted((r for r in s["grid"] if r["k"] == 10), key=lambda r: r["threshold_bits"])
    xs = [r["threshold_bits"] for r in rows]
    for key, label, color in (("poisoned_all_exposure", "Poisoned: edited text in top 3", ORANGE),
                              ("poisoned_all_hit3", "Poisoned: Hit@3", BLUE),
                              ("clean_all_hit3", "Clean: Hit@3 (cost)", AQUA)):
        left.plot(xs, [r[key] for r in rows], color=color, lw=2, label=label)
    left.axvline(deployed, color=MUTED, lw=1, ls="--")
    left.text(deployed + 0.1, 0.02, f"frozen threshold\n{deployed:.2f} bits", color=MUTED, fontsize=7)
    left.set_xlabel("Threshold (bits); candidates k = 10")
    left.set_ylabel("Share of 44 questions")
    left.set_ylim(0, 1)
    left.grid(color=GRID, lw=0.6)
    left.set_axisbelow(True)
    left.legend(loc="upper left", frameon=False, fontsize=7.5)
    depth = sorted((r for r in s["grid"] if r["threshold_bits"] == deployed), key=lambda r: r["k"])
    ks = [r["k"] for r in depth]
    for key, label, color in (("poisoned_all_exposure", "Exposure", ORANGE), ("poisoned_all_hit3", "Poisoned Hit@3", BLUE),
                              ("clean_all_hit3", "Clean Hit@3", AQUA)):
        right.plot(ks, [r[key] for r in depth], color=color, lw=2, marker="o", ms=4, label=label)
    right.set_xticks(ks)
    right.set_xlabel("Candidates retrieved (k), frozen threshold")
    right.set_ylim(0, 1)
    right.grid(color=GRID, lw=0.6)
    right.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_threshold_sweep.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    auroc_figure()
    roc_figure()
    defence_figure()
    sweep_figure()
    print(sorted(p.name for p in OUT.glob("*.png")))
