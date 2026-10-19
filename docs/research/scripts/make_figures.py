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


def family_figure():
    names = ("poisoned", "poisoned_pwws_rerun", "poisoned_adaptive", "control")
    paths = {c: RESULTS / f"entropy-family/family-{c}.json" for c in names}
    if not all(p.exists() for p in paths.values()):
        return
    res = {c: json.loads(p.read_text())["results"]["all"] for c, p in paths.items()}
    detectors = [("syngap_top3_domain", "Synonym gap, 50/50 q\n(deployed)"), ("syngap_top3_dirichlet", "Synonym gap,\nDirichlet q"),
                 ("js_domain", "Jensen-Shannon\nvs domain"), ("lm_top5_surprisal", "LM surprisal,\ntop 5 tokens"),
                 ("ctx_syngap_top3", "Contextual synonym gap\n(LM as q)")]
    series = [("poisoned", "Original PWWS", BLUE), ("poisoned_pwws_rerun", "PWWS, retrained surrogate", AQUA),
              ("poisoned_adaptive", "Adaptive PWWS", ORANGE), ("control", "Control (no substitutions)", YELLOW)]
    fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=200)
    h = 0.2
    for i, (c, label, color) in enumerate(series):
        ys = [k + (i - 1.5) * h for k in range(len(detectors))]
        vals = [res[c][d]["auroc"] for d, _ in detectors]
        bars = ax.barh(ys, vals, height=h - 0.03, color=color, label=label)
        for bar, v in zip(bars, vals):
            ax.text(v + 0.008, bar.get_y() + bar.get_height() / 2, f"{v:.2f}", va="center", fontsize=6.5, color=INK)
    ax.axvline(0.5, color=MUTED, lw=1, ls="--")
    ax.set_yticks(range(len(detectors)), [label for _, label in detectors], fontsize=8)
    ax.set_ylim(len(detectors) - 0.5, -0.6)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("AUROC for finding chunks with substituted words (0.5 = chance)")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.42, -0.14), ncol=2, frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_entropy_family.png")
    plt.close(fig)


def robustness_figure():
    """Word-frequency vs contextual synonym gap on every corpus, with document-clustered 95% intervals."""
    path = RESULTS / "detector-uncertainty/auroc-intervals.json"
    if not path.exists():
        return
    corpora = json.loads(path.read_text())["corpora"]
    rows = [("poisoned", "Original PWWS"), ("poisoned_pwws_rerun", "PWWS, retrained surrogate"),
            ("poisoned_textfooler", "TextFooler (second attack)"), ("poisoned_adaptive", "Adaptive PWWS,\nfrequency-matched"),
            ("poisoned_adaptive_lm", "Adaptive PWWS,\nfrequency + LM-matched"), ("control", "Control (layout only,\nno substitutions)")]
    rows = [(c, label) for c, label in rows if "family" in corpora.get(c, {})]
    series = [("syngap_top3_domain", "Synonym gap, word-frequency q (deployed filter)", BLUE, -0.14),
              ("ctx_syngap_top3", "Contextual synonym gap, language model as q", ORANGE, 0.14)]
    fig, ax = plt.subplots(figsize=(7.4, 0.62 * len(rows) + 1.3), dpi=200)
    for score, label, color, dy in series:
        for k, (c, _) in enumerate(rows):
            r = corpora[c]["family"]["scores"][score]
            ax.plot(r["ci95"], [k + dy, k + dy], color=color, lw=2, solid_capstyle="round")
            ax.plot([r["auroc"]], [k + dy], "o", ms=7, color=color, mec="white", mew=1.5,
                    label=label if k == 0 else None)
            ax.text(r["ci95"][1] + 0.012, k + dy, f"{r['auroc']:.2f}", va="center", fontsize=7, color=INK)
    ax.axvline(0.5, color=MUTED, lw=1, ls="--")
    ax.text(0.505, -0.75, "chance", ha="left", fontsize=7, color=MUTED)
    ax.set_yticks(range(len(rows)), [label for _, label in rows], fontsize=8)
    ax.set_ylim(len(rows) - 0.5, -0.9)
    ax.set_xlim(0.2, 1.08)
    ax.set_xlabel("AUROC for finding chunks with substituted words\n(dot; line = 95% interval, documents resampled)")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=1, frameon=False, fontsize=7.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig6_detector_robustness.png")
    plt.close(fig)


def dose_response_figure():
    """Second-order attacker: successful sections vs LM budget, with what the contextual filter catches."""
    data = ROOT / "backend/data"
    levels = [("poisoned_adaptive_lm", "0\n(strict)"), ("poisoned_adaptive_lm_budget", "4.46\n(= threshold)"),
              ("poisoned_adaptive_lm_budget_20", "20"), ("poisoned_adaptive_lm_budget_100", "100"),
              ("poisoned_adaptive_lm_budget_300", "300"), ("poisoned_pwws_rerun", "no limit\n(plain PWWS)")]
    levels = [(c, label) for c, label in levels if (data / c / "pwws_attack_manifest.jsonl").exists()]
    intervals = RESULTS / "detector-uncertainty/auroc-intervals.json"
    frozen = json.loads(intervals.read_text())["corpora"] if intervals.exists() else {}
    counts = []
    for c, _ in levels:
        lines = (data / c / "pwws_attack_manifest.jsonl").read_text().splitlines()
        counts.append(sum(json.loads(line)["success"] for line in lines if line.strip()))
    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
    bars = ax.bar(range(len(levels)), counts, width=0.6, color=BLUE)
    for k, ((c, _), bar, n) in enumerate(zip(levels, bars, counts)):
        ax.text(k, n + 0.8, f"{n} of 57", ha="center", fontsize=8, color=INK)
        ctx = frozen.get(c, {}).get("frozen_thresholds", {}).get("ctx_syngap_top3")
        if ctx and ctx["edited"]:
            ax.text(k, n + 3.6, f"filter flags\n{ctx['edited_flagged']} of {ctx['edited']} edits", ha="center",
                    fontsize=6.5, color=MUTED)
    ax.set_xticks(range(len(levels)), [label for _, label in levels], fontsize=8)
    ax.set_xlabel("How much less probable (bits, distilgpt2) the attacker may make each passage")
    ax.set_ylabel("Sections attacked successfully")
    ax.set_ylim(0, 57)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_attacker_budget.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    auroc_figure()
    roc_figure()
    defence_figure()
    sweep_figure()
    family_figure()
    robustness_figure()
    dose_response_figure()
    print(sorted(p.name for p in OUT.glob("*.png")))
