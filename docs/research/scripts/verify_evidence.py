"""Evidence check: every headline number traced to a saved file, every input and record checksummed.

Reads only saved files (no model calls, no Qdrant). For each claim used in the
dissertation, the PDD and the report for Nikos, it looks up the value in the result
file that produced it and checks it matches. It also writes a SHA-256 manifest of the
benchmark, the three corpora, the attack manifest, every run record directory and every
result file. Exit status 1 if any claim does not match or any run is incomplete.

Usage: python docs/research/scripts/verify_evidence.py   (writes docs/research/EVIDENCE.md and evidence-manifest.json)
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RES = "docs/research/results"
MAIN = f"{RES}/main-v1-20261016/summary.json"
DEF = f"{RES}/entropy-defence/live-paired/summary.json"
DET = f"{RES}/entropy-detector-20261016/detector-poisoned.json"
CTRL = f"{RES}/entropy-detector-20261016/detector-control.json"
SWEEP = f"{RES}/entropy-defence/threshold-sweep/sweep.json"
REP = f"{RES}/entropy-repair/live-paired/summary.json"
FAM = f"{RES}/entropy-family"
RUNS = (
    "pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e",
    "pilot-runs/20261017T165331Z-defence-cebfb27c1e9048cdb61fbfe15f37e50d",
    "pilot-runs/20261018T101453Z-repair-525ce73351064f089bdb62a448ee447c",
    "pilot-runs/20261018T180113Z-contextual-a2eb543b82974c5aa4c1502de6e555a7",
    "pilot-runs/20261019T200355Z-evidence-check-f8780367874442dc8b90160c2d51a463",
    "pilot-runs/20261019T200851Z-textfooler-33c7d2a707874d2ca57cb5b7851984e9",
    "pilot-runs/20261027T225951Z-monitor-7435694678804a8fb151bed0f2cb853d",
)
CTX = f"{RES}/contextual-defence/live-paired/summary.json"
DIAG = f"{RES}/adaptive-attack/second-order-diagnostic.json"
IV = f"{RES}/detector-uncertainty/auroc-intervals.json"
EC = f"{RES}/evidence-check/summary.json"
TF = f"{RES}/textfooler-defence/summary.json"
PB = f"{RES}/detector-uncertainty/perplexity-baseline.json"
JA = f"{RES}/judge-agreement/agreement.json"
MD = f"{RES}/runtime-monitor/dry-check.json"
MO = f"{RES}/runtime-monitor/live/summary.json"


def manifest_count(corpus, result):
    def count(_):
        lines = (
            (ROOT / f"backend/data/{corpus}/pwws_attack_manifest.jsonl")
            .read_text()
            .splitlines()
        )
        return sum(
            json.loads(line)["result"] == result for line in lines if line.strip()
        )

    return count


def deployed(rows):
    return next(r for r in rows if r["deployed"])


# (claim, file, path into the JSON (keys, or a function), expected value as quoted in the write-ups)
CLAIMS = [
    (
        "Main run: clean correctness",
        MAIN,
        ["strata", "all", "correctness", "clean"],
        0.714,
    ),
    (
        "Main run: poisoned correctness",
        MAIN,
        ["strata", "all", "correctness", "poisoned"],
        0.5549,
    ),
    (
        "Main run: correctness drop",
        MAIN,
        ["strata", "all", "correctness", "delta"],
        -0.1591,
    ),
    (
        "Main run: drop on perturbed targets",
        MAIN,
        ["strata", "target_perturbed", "correctness", "delta"],
        -0.25,
    ),
    (
        "Main run: drop on unperturbed targets",
        MAIN,
        ["strata", "target_not_perturbed", "correctness", "delta"],
        -0.0147,
    ),
    (
        "Main run: ASR (section exposure)",
        MAIN,
        ["strata", "all", "asr_section_0.25"],
        0.2803,
    ),
    (
        "Main run: ASR (edited-text exposure)",
        MAIN,
        ["strata", "all", "asr_edited_0.25"],
        0.1667,
    ),
    ("Main run: poisoned abstentions", MAIN, ["outcomes", "poisoned", "abstained"], 45),
    (
        "Main run: poisoned confident errors",
        MAIN,
        ["outcomes", "poisoned", "incorrect"],
        2,
    ),
    (
        "Detector: synonym gap vs domain, AUROC all",
        DET,
        ["results", "all", "syngap_top3_domain", "auroc"],
        0.82,
    ),
    (
        "Detector: synonym gap vs domain, AUROC held-out",
        DET,
        ["results", "held_out", "syngap_top3_domain", "auroc"],
        0.94,
    ),
    (
        "Detector: letter-frequency KL, AUROC all",
        DET,
        ["results", "all", "char_kl", "auroc"],
        0.33,
    ),
    (
        "Detector: word KL vs domain, AUROC all",
        DET,
        ["results", "all", "kl_domain", "auroc"],
        0.72,
    ),
    (
        "Detector: synonym gap on control corpus, AUROC",
        CTRL,
        ["results", "all", "syngap_top3_domain", "auroc"],
        0.67,
    ),
    (
        "Detector: frozen threshold (bits)",
        DET,
        ["results", "development", "syngap_top3_domain", "threshold_fpr10"],
        7.2262,
    ),
    (
        "Matched control: syngap higher in edited chunk",
        f"{RES}/entropy-defence/matched-control.json",
        ["scores", "syngap_top3_domain", "poisoned_higher"],
        38,
    ),
    (
        "Explanations: flagged edited chunks",
        f"{RES}/entropy-defence/explanations.json",
        ["summary", "flagged_edited_chunks"],
        27,
    ),
    (
        "Explanations: cite a real substitution",
        f"{RES}/entropy-defence/explanations.json",
        ["summary", "evidence_includes_real_substitution"],
        25,
    ),
    (
        "Explanations: name the exact original",
        f"{RES}/entropy-defence/explanations.json",
        ["summary", "explanation_names_exact_original"],
        22,
    ),
    (
        "Defence: exposure, poisoned",
        DEF,
        ["comparisons", "defended_vs_poisoned", "all", "exposure", "b"],
        0.4091,
    ),
    (
        "Defence: exposure, defended",
        DEF,
        ["comparisons", "defended_vs_poisoned", "all", "exposure", "a"],
        0.2727,
    ),
    (
        "Defence: exposure change, Wilcoxon p",
        DEF,
        ["comparisons", "defended_vs_poisoned", "all", "exposure", "wilcoxon_p"],
        0.0312,
    ),
    (
        "Defence: correctness change vs poisoned",
        DEF,
        ["comparisons", "defended_vs_poisoned", "all", "correctness", "delta"],
        -0.0284,
    ),
    (
        "Defence: correctness change on perturbed targets",
        DEF,
        [
            "comparisons",
            "defended_vs_poisoned",
            "target_perturbed",
            "correctness",
            "delta",
        ],
        -0.071,
    ),
    (
        "Defence: cost on clean correctness",
        DEF,
        ["comparisons", "clean_filtered_vs_clean", "all", "correctness", "delta"],
        -0.0644,
    ),
    (
        "Defence: confident errors, defended",
        DEF,
        ["outcomes", "defended", "incorrect"],
        0,
    ),
    ("Defence: abstentions, defended", DEF, ["outcomes", "defended", "abstained"], 53),
    (
        "Defence: ASR (edited exposure), defended",
        DEF,
        ["asr_edited_exposure", "defended"],
        0.1061,
    ),
    (
        "Sweep: deployed setting reproduces live exposure",
        SWEEP,
        [lambda s: deployed(s["grid"])["poisoned_all_exposure"]],
        0.2727,
    ),
    (
        "Sweep: unfiltered poisoned exposure",
        SWEEP,
        ["unfiltered_top3", "poisoned_exposure"],
        0.4091,
    ),
    (
        "Repair: correctness, repaired",
        REP,
        ["comparisons", "repaired_vs_defended", "all", "correctness", "a"],
        0.506,
    ),
    (
        "Repair: correctness change vs drop defence",
        REP,
        ["comparisons", "repaired_vs_defended", "all", "correctness", "delta"],
        -0.021,
    ),
    (
        "Repair: edited text reaching the model",
        REP,
        ["comparisons", "repaired_vs_poisoned", "all", "exposure", "a"],
        0.364,
    ),
    ("Repair: confident errors", REP, ["outcomes", "repaired", "incorrect"], 0),
    ("Repair: ASR (edited exposure)", REP, ["asr_edited_exposure", "repaired"], 0.1818),
    (
        "Contextual synonym gap, poisoned corpus, AUROC",
        f"{FAM}/family-poisoned.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.95,
    ),
    (
        "Contextual synonym gap, held-out, AUROC",
        f"{FAM}/family-poisoned.json",
        ["results", "held_out", "ctx_syngap_top3", "auroc"],
        0.88,
    ),
    (
        "Contextual synonym gap, formatting-only control, AUROC",
        f"{FAM}/family-control.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.53,
    ),
    (
        "Contextual synonym gap, adaptive attack, AUROC",
        f"{FAM}/family-poisoned_adaptive.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.92,
    ),
    (
        "Deployed synonym gap, adaptive attack, AUROC",
        f"{FAM}/detector-poisoned_adaptive.json",
        ["results", "all", "syngap_top3_domain", "auroc"],
        0.47,
    ),
    (
        "Jensen-Shannon, poisoned corpus, AUROC",
        f"{FAM}/family-poisoned.json",
        ["results", "all", "js_domain", "auroc"],
        0.47,
    ),
    (
        "Dirichlet synonym gap, poisoned corpus, AUROC",
        f"{FAM}/family-poisoned.json",
        ["results", "all", "syngap_top3_dirichlet", "auroc"],
        0.83,
    ),
    (
        "Matched control: deployed synonym gap AUROC",
        f"{FAM}/detector-poisoned_pwws_rerun.json",
        ["results", "all", "syngap_top3_domain", "auroc"],
        0.88,
    ),
    (
        "Matched control: contextual synonym gap AUROC",
        f"{FAM}/family-poisoned_pwws_rerun.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.97,
    ),
    (
        "Adaptive attack: successful sections",
        f"{RES}/adaptive-attack/surrogate-and-attack-record.json",
        ["adaptive_attack", "successful"],
        8,
    ),
    (
        "Sweep: deployed setting keeps clean Hit@3",
        SWEEP,
        [lambda s: deployed(s["grid"])["clean_all_hit3"]],
        0.7045,
    ),
    (
        "Contextual defence: exposure, contextual",
        CTX,
        ["comparisons", "contextual_vs_poisoned", "all", "exposure", "a"],
        0.204,
    ),
    (
        "Contextual defence: exposure change, Wilcoxon p",
        CTX,
        ["comparisons", "contextual_vs_poisoned", "all", "exposure", "wilcoxon_p"],
        0.012,
    ),
    (
        "Contextual defence: correctness, contextual",
        CTX,
        ["comparisons", "contextual_vs_poisoned", "all", "correctness", "a"],
        0.485,
    ),
    (
        "Contextual defence: correctness change, Wilcoxon p",
        CTX,
        ["comparisons", "contextual_vs_poisoned", "all", "correctness", "wilcoxon_p"],
        0.020,
    ),
    (
        "Contextual defence: cost on clean correctness",
        CTX,
        ["comparisons", "clean_contextual_vs_clean", "all", "correctness", "delta"],
        -0.013,
    ),
    (
        "Contextual defence: confident errors",
        CTX,
        ["outcomes", "contextual", "incorrect"],
        0,
    ),
    (
        "Contextual defence: abstentions",
        CTX,
        ["outcomes", "contextual", "abstained"],
        63,
    ),
    (
        "Contextual defence: ASR (edited exposure)",
        CTX,
        ["asr_edited_exposure", "contextual"],
        0.1136,
    ),
    (
        "TextFooler: successful sections",
        "backend/data/poisoned_textfooler/pwws_attack_manifest.jsonl",
        [manifest_count("poisoned_textfooler", "SuccessfulAttackResult")],
        49,
    ),
    (
        "TextFooler: deployed synonym gap AUROC",
        f"{FAM}/detector-poisoned_textfooler.json",
        ["results", "all", "syngap_top3_domain", "auroc"],
        0.90,
    ),
    (
        "TextFooler: contextual synonym gap AUROC",
        f"{FAM}/family-poisoned_textfooler.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.91,
    ),
    (
        "Second-order (strict): successful sections",
        "backend/data/poisoned_adaptive_lm/pwws_attack_manifest.jsonl",
        [manifest_count("poisoned_adaptive_lm", "SuccessfulAttackResult")],
        0,
    ),
    (
        "Second-order (4.46-bit budget): successful sections",
        "backend/data/poisoned_adaptive_lm_budget/pwws_attack_manifest.jsonl",
        [manifest_count("poisoned_adaptive_lm_budget", "SuccessfulAttackResult")],
        0,
    ),
    ("Diagnostic: swaps used by unrestricted PWWS", DIAG, ["summary", "swaps"], 550),
    ("Diagnostic: swaps passing the LM rule", DIAG, ["summary", "pass_lm_rule"], 9),
    ("Diagnostic: swaps passing both rules", DIAG, ["summary", "pass_both_rules"], 5),
    (
        "Diagnostic: median LM cost of a swap (bits)",
        DIAG,
        ["summary", "median_lm_delta_bits"],
        -17.861,
    ),
    (
        "Second-order (20-bit budget): successful sections",
        "backend/data/poisoned_adaptive_lm_budget_20/pwws_attack_manifest.jsonl",
        [manifest_count("poisoned_adaptive_lm_budget_20", "SuccessfulAttackResult")],
        0,
    ),
    (
        "Second-order (100-bit budget): successful sections",
        "backend/data/poisoned_adaptive_lm_budget_100/pwws_attack_manifest.jsonl",
        [manifest_count("poisoned_adaptive_lm_budget_100", "SuccessfulAttackResult")],
        5,
    ),
    (
        "Second-order (300-bit budget): successful sections",
        "backend/data/poisoned_adaptive_lm_budget_300/pwws_attack_manifest.jsonl",
        [manifest_count("poisoned_adaptive_lm_budget_300", "SuccessfulAttackResult")],
        8,
    ),
    (
        "Second-order (100-bit): contextual gap AUROC",
        f"{FAM}/family-poisoned_adaptive_lm_budget_100.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.78,
    ),
    (
        "Second-order (300-bit): contextual gap AUROC",
        f"{FAM}/family-poisoned_adaptive_lm_budget_300.json",
        ["results", "all", "ctx_syngap_top3", "auroc"],
        0.92,
    ),
    (
        "Intervals: contextual minus word-frequency AUROC, PWWS",
        IV,
        [
            "corpora",
            "poisoned",
            "family",
            "scores",
            "ctx_syngap_top3_minus_syngap_top3_domain",
            "difference",
        ],
        0.131,
    ),
    (
        "Intervals: contextual AUROC on PWWS, lower bound",
        IV,
        ["corpora", "poisoned", "family", "scores", "ctx_syngap_top3", "ci95", 0],
        0.87,
    ),
    (
        "Frozen contextual threshold: TextFooler edits flagged",
        IV,
        [
            "corpora",
            "poisoned_textfooler",
            "frozen_thresholds",
            "ctx_syngap_top3",
            "edited_flagged",
        ],
        70,
    ),
    (
        "Frozen contextual threshold: first-order adaptive edits flagged",
        IV,
        [
            "corpora",
            "poisoned_adaptive",
            "frozen_thresholds",
            "ctx_syngap_top3",
            "edited_flagged",
        ],
        10,
    ),
    (
        "Monitor dry check: clean answers with any violation (all refusals, phi2; phi1 flags none)",
        MD,
        ["counts", "clean", "any_violation"],
        26,
    ),
    (
        "Monitor dry check: poisoned phi1 flags",
        MD,
        ["counts", "poisoned", "phi1_lexical"],
        3,
    ),
    (
        "Monitor verify: exposure",
        MO,
        ["comparisons", "monitor_vs_poisoned", "exposure", "a"],
        0.280,
    ),
    (
        "Monitor verify: exposure p",
        MO,
        ["comparisons", "monitor_vs_poisoned", "exposure", "wilcoxon_p"],
        0.0156,
    ),
    (
        "Monitor verify vs contextual: correctness delta",
        MO,
        ["comparisons", "monitor_vs_contextual", "correctness", "delta"],
        0.040,
    ),
    (
        "Monitor restore: correctness",
        MO,
        ["comparisons", "monitor_restore_vs_poisoned", "correctness", "a"],
        0.773,
    ),
    (
        "Monitor restore: correctness delta",
        MO,
        ["comparisons", "monitor_restore_vs_poisoned", "correctness", "delta"],
        0.218,
    ),
    ("Monitor restore: refusals", MO, ["outcomes", "monitor_restore", "abstained"], 7),
    (
        "Monitor clean cost",
        MO,
        ["comparisons", "clean_monitor_vs_clean", "correctness", "delta"],
        -0.013,
    ),
    (
        "Monitor clean: quarantined passages",
        MO,
        ["monitor", "clean_monitor", "quarantined_passages"],
        0,
    ),
    (
        "Monitor TextFooler: exposure delta",
        MO,
        ["comparisons", "textfooler_monitor_vs_textfooler", "exposure", "delta"],
        -0.235,
    ),
    (
        "Monitor TextFooler: quarantined with edited text",
        MO,
        ["monitor", "textfooler_monitor", "quarantined_with_edited_text"],
        26,
    ),
    (
        "Monitor PWWS: quarantined with edited text",
        MO,
        ["monitor", "monitor", "quarantined_with_edited_text"],
        10,
    ),
    (
        "Monitor: phi3 trace violations (PWWS verify)",
        MO,
        ["monitor", "monitor", "phi3_trace_violations"],
        0,
    ),
    ("Judge check: weighted kappa", JA, ["all", "quadratic_weighted_kappa"], 0.816),
    ("Judge check: Spearman", JA, ["all", "spearman"], 0.853),
    ("Judge check: within 0.25", JA, ["all", "within_0.25"], 0.827),
    ("Judge check: judge minus human", JA, ["all", "judge_minus_human_mean"], 0.077),
    ("Judge check: items graded", JA, ["graded"], 75),
    (
        "Perplexity baseline: top-5 surprisal AUROC, PWWS",
        PB,
        ["corpora", "poisoned", "scores", "lm_top5_surprisal", "auroc"],
        0.909,
    ),
    (
        "Perplexity baseline: mean surprisal AUROC, PWWS",
        PB,
        ["corpora", "poisoned", "scores", "lm_mean_surprisal", "auroc"],
        0.768,
    ),
    (
        "Perplexity baseline: contextual minus mean, PWWS",
        PB,
        [
            "corpora",
            "poisoned",
            "scores",
            "ctx_syngap_top3_minus_lm_mean_surprisal",
            "difference",
        ],
        0.181,
    ),
    (
        "Perplexity baseline: contextual minus top-5, PWWS",
        PB,
        [
            "corpora",
            "poisoned",
            "scores",
            "ctx_syngap_top3_minus_lm_top5_surprisal",
            "difference",
        ],
        0.040,
    ),
    (
        "Perplexity baseline: top-5 surprisal AUROC, TextFooler",
        PB,
        ["corpora", "poisoned_textfooler", "scores", "lm_top5_surprisal", "auroc"],
        0.922,
    ),
    (
        "TextFooler live: exposure without defence",
        TF,
        ["comparisons", "textfooler_contextual_vs_textfooler", "all", "exposure", "b"],
        0.818,
    ),
    (
        "TextFooler live: exposure with contextual filter",
        TF,
        ["comparisons", "textfooler_contextual_vs_textfooler", "all", "exposure", "a"],
        0.523,
    ),
    (
        "TextFooler live: contextual exposure change, Wilcoxon p",
        TF,
        [
            "comparisons",
            "textfooler_contextual_vs_textfooler",
            "all",
            "exposure",
            "wilcoxon_p",
        ],
        0.0002,
    ),
    (
        "TextFooler live: exposure with word-frequency filter",
        TF,
        ["comparisons", "textfooler_defended_vs_textfooler", "all", "exposure", "a"],
        0.795,
    ),
    (
        "TextFooler live: correctness drop vs clean",
        TF,
        ["comparisons", "textfooler_vs_clean", "all", "correctness", "delta"],
        -0.150,
    ),
    (
        "TextFooler live: refusals with contextual filter",
        TF,
        ["outcomes", "textfooler_contextual", "abstained"],
        74,
    ),
    (
        "Evidence check: precision (error = not correct)",
        EC,
        ["primary_error_not_correct", "precision"],
        0.28,
    ),
    ("Evidence check: recall", EC, ["primary_error_not_correct", "recall"], 0.20),
    (
        "Evidence check: false-alarm rate",
        EC,
        ["primary_error_not_correct", "false_alarm"],
        0.31,
    ),
    (
        "Evidence check: partial answers fully supported",
        EC,
        ["outcome_by_label", "partial", "supported"],
        68,
    ),
    (
        "Frozen contextual threshold: PWWS edits flagged",
        IV,
        [
            "corpora",
            "poisoned",
            "frozen_thresholds",
            "ctx_syngap_top3",
            "edited_flagged",
        ],
        42,
    ),
]


def lookup(data, path):
    for step in path:
        data = step(data) if callable(step) else data[step]
    return data


def matches(found, expected):
    if isinstance(expected, int) and not isinstance(expected, bool):
        return found == expected
    decimals = len(repr(expected).split(".")[1]) if "." in repr(expected) else 0
    return round(float(found), decimals) == expected


def sha256_of(path):
    digest = hashlib.sha256()
    files = (
        sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    )
    for f in files:
        digest.update(
            f.relative_to(path if path.is_dir() else path.parent).as_posix().encode()
        )
        digest.update(f.read_bytes())
    return digest.hexdigest(), len(files)


def main():
    failures, lines = 0, []
    for claim, file, path, expected in CLAIMS:
        data = (
            None if file.endswith(".jsonl") else json.loads((ROOT / file).read_text())
        )  # .jsonl claims count lines
        found = lookup(data, path)
        ok = matches(found, expected)
        failures += not ok
        lines.append(
            f"| {claim} | {expected} | {found} | {'ok' if ok else 'MISMATCH'} | `{file}` |"
        )
    runs = []
    for run in RUNS:
        completion = json.loads((ROOT / run / "completion.json").read_text())
        recorded = completion["record_sha256"]
        unchanged = sum(
            hashlib.sha256(
                (ROOT / run / "observations" / name).read_bytes()
            ).hexdigest()
            == digest
            for name, digest in recorded.items()
            if (ROOT / run / "observations" / name).exists()
        )
        present = len(list((ROOT / run / "observations").glob("*.json")))
        intact = unchanged == len(recorded) == present
        failures += not intact
        runs.append(
            f"| `{run}` | {completion['finished_at']} | {present} | {unchanged} of {len(recorded)} | {'ok' if intact else 'CHANGED'} |"
        )
    inputs = {
        "benchmark v1": "backend/data/evaluation/questions_v1.json",
        "clean corpus": "backend/data/raw/knowledge_base",
        "poisoned corpus": "backend/data/poisoned/knowledge_base",
        "formatting-only control corpus": "backend/data/control/knowledge_base",
        "PWWS attack manifest": "backend/data/poisoned/pwws_attack_manifest.jsonl",
        "adaptive-attack corpus": "backend/data/poisoned_adaptive/knowledge_base",
        "adaptive-attack manifest": "backend/data/poisoned_adaptive/pwws_attack_manifest.jsonl",
        "matched-control corpus": "backend/data/poisoned_pwws_rerun/knowledge_base",
        "matched-control manifest": "backend/data/poisoned_pwws_rerun/pwws_attack_manifest.jsonl",
        "entropy-filter defence code": "backend/app/defence/entropy_filter.py",
        "contextual-filter defence code": "backend/app/defence/contextual_filter.py",
        **{
            f"{c} corpus and manifest": f"backend/data/{c}"
            for c in (
                "poisoned_textfooler",
                "poisoned_adaptive_lm",
                "poisoned_adaptive_lm_budget",
                "poisoned_adaptive_lm_budget_20",
                "poisoned_adaptive_lm_budget_100",
            )
            if (ROOT / f"backend/data/{c}/pwws_attack_manifest.jsonl").exists()
        },
        **{f"run {Path(r).name}": r for r in RUNS},
        **{
            f"results {p.relative_to(ROOT / RES)}": str(p.relative_to(ROOT))
            for p in sorted((ROOT / RES).rglob("*"))
            if p.is_file()
        },
    }
    manifest = {}
    for name, rel in inputs.items():
        digest, count = sha256_of(ROOT / rel)
        manifest[name] = {"path": rel, "sha256": digest, "files": count}
    (ROOT / "docs/research/evidence-manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n"
    )
    doc = [
        "# Evidence index",
        "",
        "Generated by `python docs/research/scripts/verify_evidence.py` from saved files only. "
        "Every number below is read from the result file named next to it and compared with the value quoted "
        "in the dissertation, the PDD and the report for Nikos.",
        "",
        f"**{sum('| ok |' in l for l in lines)} of {len(CLAIMS)} claims match; "
        f"{'every run record is unchanged since its run finished' if not failures else 'see problems below'}.**",
        "",
        "## Claims",
        "",
        "| Claim | Quoted | In file | Check | Source |",
        "|---|---|---|---|---|",
        *lines,
        "",
        "## Run records",
        "",
        "Each record is re-hashed and compared with the SHA-256 the runner wrote in `completion.json` when the run finished.",
        "",
        "| Run | Finished | Records | Unchanged since run | Check |",
        "|---|---|---|---|---|",
        *runs,
        "",
        "## Checksums",
        "",
        "SHA-256 over file names and contents (directories in sorted order). "
        "Full list in `docs/research/evidence-manifest.json`.",
        "",
        "| Item | Files | SHA-256 (first 16) |",
        "|---|---|---|",
        *[
            f"| {n} | {m['files']} | `{m['sha256'][:16]}` |"
            for n, m in manifest.items()
            if not n.startswith("results ")
        ],
        "",
    ]
    (ROOT / "docs/research/EVIDENCE.md").write_text("\n".join(doc))
    print("\n".join(lines + runs))
    print(f"{failures} problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
