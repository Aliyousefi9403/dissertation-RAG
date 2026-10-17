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
RUNS = ("pilot-runs/20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e",
        "pilot-runs/20261017T165331Z-defence-cebfb27c1e9048cdb61fbfe15f37e50d")


def deployed(rows):
    return next(r for r in rows if r["deployed"])


# (claim, file, path into the JSON (keys, or a function), expected value as quoted in the write-ups)
CLAIMS = [
    ("Main run: clean correctness", MAIN, ["strata", "all", "correctness", "clean"], 0.714),
    ("Main run: poisoned correctness", MAIN, ["strata", "all", "correctness", "poisoned"], 0.5549),
    ("Main run: correctness drop", MAIN, ["strata", "all", "correctness", "delta"], -0.1591),
    ("Main run: drop on perturbed targets", MAIN, ["strata", "target_perturbed", "correctness", "delta"], -0.25),
    ("Main run: drop on unperturbed targets", MAIN, ["strata", "target_not_perturbed", "correctness", "delta"], -0.0147),
    ("Main run: ASR (section exposure)", MAIN, ["strata", "all", "asr_section_0.25"], 0.2803),
    ("Main run: ASR (edited-text exposure)", MAIN, ["strata", "all", "asr_edited_0.25"], 0.1667),
    ("Main run: poisoned abstentions", MAIN, ["outcomes", "poisoned", "abstained"], 45),
    ("Main run: poisoned confident errors", MAIN, ["outcomes", "poisoned", "incorrect"], 2),
    ("Detector: synonym gap vs domain, AUROC all", DET, ["results", "all", "syngap_top3_domain", "auroc"], 0.82),
    ("Detector: synonym gap vs domain, AUROC held-out", DET, ["results", "held_out", "syngap_top3_domain", "auroc"], 0.94),
    ("Detector: letter-frequency KL, AUROC all", DET, ["results", "all", "char_kl", "auroc"], 0.33),
    ("Detector: word KL vs domain, AUROC all", DET, ["results", "all", "kl_domain", "auroc"], 0.72),
    ("Detector: synonym gap on control corpus, AUROC", CTRL, ["results", "all", "syngap_top3_domain", "auroc"], 0.67),
    ("Detector: frozen threshold (bits)", DET, ["results", "development", "syngap_top3_domain", "threshold_fpr10"], 7.2262),
    ("Matched control: syngap higher in edited chunk", f"{RES}/entropy-defence/matched-control.json",
     ["scores", "syngap_top3_domain", "poisoned_higher"], 38),
    ("Explanations: flagged edited chunks", f"{RES}/entropy-defence/explanations.json", ["summary", "flagged_edited_chunks"], 27),
    ("Explanations: cite a real substitution", f"{RES}/entropy-defence/explanations.json", ["summary", "evidence_includes_real_substitution"], 25),
    ("Explanations: name the exact original", f"{RES}/entropy-defence/explanations.json", ["summary", "explanation_names_exact_original"], 22),
    ("Defence: exposure, poisoned", DEF, ["comparisons", "defended_vs_poisoned", "all", "exposure", "b"], 0.4091),
    ("Defence: exposure, defended", DEF, ["comparisons", "defended_vs_poisoned", "all", "exposure", "a"], 0.2727),
    ("Defence: exposure change, Wilcoxon p", DEF, ["comparisons", "defended_vs_poisoned", "all", "exposure", "wilcoxon_p"], 0.0312),
    ("Defence: correctness change vs poisoned", DEF, ["comparisons", "defended_vs_poisoned", "all", "correctness", "delta"], -0.0284),
    ("Defence: correctness change on perturbed targets", DEF,
     ["comparisons", "defended_vs_poisoned", "target_perturbed", "correctness", "delta"], -0.071),
    ("Defence: cost on clean correctness", DEF, ["comparisons", "clean_filtered_vs_clean", "all", "correctness", "delta"], -0.0644),
    ("Defence: confident errors, defended", DEF, ["outcomes", "defended", "incorrect"], 0),
    ("Defence: abstentions, defended", DEF, ["outcomes", "defended", "abstained"], 53),
    ("Defence: ASR (edited exposure), defended", DEF, ["asr_edited_exposure", "defended"], 0.1061),
    ("Sweep: deployed setting reproduces live exposure", SWEEP, [lambda s: deployed(s["grid"])["poisoned_all_exposure"]], 0.2727),
    ("Sweep: unfiltered poisoned exposure", SWEEP, ["unfiltered_top3", "poisoned_exposure"], 0.4091),
    ("Sweep: deployed setting keeps clean Hit@3", SWEEP, [lambda s: deployed(s["grid"])["clean_all_hit3"]], 0.7045),
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
    files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    for f in files:
        digest.update(f.relative_to(path if path.is_dir() else path.parent).as_posix().encode())
        digest.update(f.read_bytes())
    return digest.hexdigest(), len(files)


def main():
    failures, lines = 0, []
    for claim, file, path, expected in CLAIMS:
        found = lookup(json.loads((ROOT / file).read_text()), path)
        ok = matches(found, expected)
        failures += not ok
        lines.append(f"| {claim} | {expected} | {found} | {'ok' if ok else 'MISMATCH'} | `{file}` |")
    runs = []
    for run in RUNS:
        completion = json.loads((ROOT / run / "completion.json").read_text())
        recorded = completion["record_sha256"]
        unchanged = sum(hashlib.sha256((ROOT / run / "observations" / name).read_bytes()).hexdigest() == digest
                        for name, digest in recorded.items() if (ROOT / run / "observations" / name).exists())
        present = len(list((ROOT / run / "observations").glob("*.json")))
        intact = unchanged == len(recorded) == present
        failures += not intact
        runs.append(f"| `{run}` | {completion['finished_at']} | {present} | {unchanged} of {len(recorded)} | {'ok' if intact else 'CHANGED'} |")
    inputs = {
        "benchmark v1": "backend/data/evaluation/questions_v1.json",
        "clean corpus": "backend/data/raw/knowledge_base",
        "poisoned corpus": "backend/data/poisoned/knowledge_base",
        "formatting-only control corpus": "backend/data/control/knowledge_base",
        "PWWS attack manifest": "backend/data/poisoned/pwws_attack_manifest.jsonl",
        "entropy-filter defence code": "backend/app/defence/entropy_filter.py",
        **{f"run {Path(r).name}": r for r in RUNS},
        **{f"results {p.relative_to(ROOT / RES)}": str(p.relative_to(ROOT)) for p in sorted((ROOT / RES).rglob("*")) if p.is_file()},
    }
    manifest = {}
    for name, rel in inputs.items():
        digest, count = sha256_of(ROOT / rel)
        manifest[name] = {"path": rel, "sha256": digest, "files": count}
    (ROOT / "docs/research/evidence-manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    doc = ["# Evidence index", "",
           "Generated by `python docs/research/scripts/verify_evidence.py` from saved files only. "
           "Every number below is read from the result file named next to it and compared with the value quoted "
           "in the dissertation, the PDD and the report for Nikos.", "",
           f"**{sum('| ok |' in l for l in lines)} of {len(CLAIMS)} claims match; "
           f"{'every run record is unchanged since its run finished' if not failures else 'see problems below'}.**", "",
           "## Claims", "", "| Claim | Quoted | In file | Check | Source |", "|---|---|---|---|---|", *lines, "",
           "## Run records", "", "Each record is re-hashed and compared with the SHA-256 the runner wrote in `completion.json` when the run finished.", "", "| Run | Finished | Records | Unchanged since run | Check |", "|---|---|---|---|---|", *runs, "",
           "## Checksums", "", "SHA-256 over file names and contents (directories in sorted order). "
           "Full list in `docs/research/evidence-manifest.json`.", "",
           "| Item | Files | SHA-256 (first 16) |", "|---|---|---|",
           *[f"| {n} | {m['files']} | `{m['sha256'][:16]}` |" for n, m in manifest.items() if not n.startswith("results ")], ""]
    (ROOT / "docs/research/EVIDENCE.md").write_text("\n".join(doc))
    print("\n".join(lines + runs))
    print(f"{failures} problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
