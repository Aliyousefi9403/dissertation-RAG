# Journal roadmap (branch `tdsc`)

The dissertation version is frozen on branch `dissertation-v1.0` (commit `51884f6`, same as `main`).
Nothing on this branch changes that version, its run records or its results. New work adds new
files, new corpora under new folder names, new vector collections under new names and new run
folders.

## Work packages

| # | Package | Answers which reviewer question | Touches backend? | Cost |
|---|---|---|---|---|
| W1 | Larger reference language models (gpt2, gpt2-medium) for the contextual detector | "Does the result depend on distilgpt2?" | No (offline script) | none |
| W2 | Monitor blame step v3: blame with the contextual synonym gap instead of rare words | "The monitor quarantines clean passages" | Yes | about £4 per live run |
| W3 | Stronger attackers: one that optimises against the detector score; a masked-language-model attack (BAE) | "Adaptive attacker is too weak" | New attack scripts and new corpora | none (CPU time) |
| W4 | Larger knowledge base (about 60 attack types) and benchmark v2 (about 150 questions) | "One small dataset" | Yes (new corpus, new collections) | about £10 per full run |
| W5 | More generator models (one larger OpenAI model, one open model) | "One LLM" | Small config change | about £10–20 |
| W6 | Second human grader for the judge check | "Only one grader" | No | none (needs a person) |
| W7 | Properties written in LTL with a generated monitor | "Is this really runtime verification?" | Yes | none |

Order: W1 (running) → W2 → W3 → W4 → W5, with W6 and W7 in parallel when people are available.

## Rules for this branch

- Every experiment writes a new run folder with create-only records and a completion manifest.
- Thresholds for new experiments are fixed on development data before held-out data is scored.
- Negative results are reported.
- `verify_evidence.py` must report 0 problems before each commit.
