# Evidence check (experimental) — detection batch 1

`POST /guarded-chat` drafts an answer with the **unchanged** baseline RAG
pipeline. A separate verifier call then checks each claim in the draft
against the retrieved chunks. The verifier output is validated strictly, a
versioned release policy is applied, and every request is written to a
create-only audit record.

This is an **experimental evidence-support baseline, not a validated poison
detector**. "Supported" only means that the retrieved text states the claim.
A poisoned source can support a false answer, and support is not evidence
that the corpus is clean. No confidence percentage is produced.

## Policy `evidence-guard-policy-v1`

| Situation | Outcome | Draft |
|---|---|---|
| ≥1 claim, every claim supported by a quotation found verbatim in a cited source | `supported` | released |
| any claim contradicted | `contradicted` | withheld |
| any claim unsupported | `unsupported` | withheld |
| fabricated or unverifiable quotation, unknown source ID, supported/contradicted with no quotation | `unavailable` (per claim) | withheld |
| no evidence retrieved, retrieval/draft/verifier failure or timeout, malformed verifier JSON, zero claims | `unavailable` | withheld |

Precedence: contradicted > unsupported > unavailable.

The verifier receives only the question, the draft and the chunk text, under
neutral IDs (`S1`, `S2`, …). It never sees file paths, metadata, reference
answers, clean counterparts or attack labels.

## What is unchanged

`/chat`, `/compare` and the history endpoints, the baseline prompt,
`RETRIEVAL_TOP_K`, chunking, embeddings, the model and temperature, existing
metrics, `create_llm()` defaults, every corpus and Qdrant collection, and the
`defended` collection. This route accepts only the `clean` and `poisoned`
states. The draft call uses the baseline model, prompt and temperature; it
only adds a request timeout (`GUARD_DRAFT_TIMEOUT_SECONDS`, default 30) and
bounded retries (`GUARD_MODEL_MAX_RETRIES`, default 1). The verifier runs at
temperature 0 with a timeout (`GUARD_VERIFIER_TIMEOUT_SECONDS`, default 45).

## Audit records

Each record is written to `backend/data/evidence_guard_audit/<run_id>.json`,
or to the directory in `GUARD_AUDIT_DIR` if set. A record holds the question,
state, retrieved evidence, draft, verifier prompt, raw verifier response,
parsed findings, decision, model settings, timings, failures and policy
version.

Writes are create-only: the record is written to an exclusive temporary file,
fsync'd, then hard-linked into place, so an existing record is never
overwritten. The API key and `sk-…` patterns are redacted. If the write
fails, the response reports `audit.saved = false` and the UI shows
"Audit record NOT saved".

## Rollback

All of this batch's backend code is in `backend/app/defence/` and its two test
files. The only edit to existing backend code is the router registration in
`main.py`. To reverse only this batch while keeping other work:

```bash
# backend
git rm -r backend/app/defence backend/tests/test_evidence_guard.py backend/tests/test_guarded_chat.py
# then delete the two marked lines in backend/app/main.py:
#   from app.defence.router import router as evidence_guard_router
#   app.include_router(evidence_guard_router)

# frontend: new files
git rm frontend-next/components/answer/EvidenceCheckCard.tsx \
       frontend-next/components/experiment/EvidenceCheckToggle.tsx \
       frontend-next/lib/api/guardedChat.ts frontend-next/lib/types/guardedChat.ts \
       frontend-next/lib/evidence/citations.ts frontend-next/e2e/evidence-check.spec.ts
# frontend: modified files, restored from the commit before this batch
git checkout <pre-batch-commit> -- frontend-next/app/page.tsx frontend-next/app/globals.css \
  frontend-next/hooks/useChatSession.ts frontend-next/lib/state/chatMachine.ts \
  frontend-next/components/answer/AnswerPanel.tsx frontend-next/components/answer/ReportMetrics.tsx \
  frontend-next/components/evidence/EvidencePanel.tsx frontend-next/components/status/PlatformStatusBar.tsx \
  frontend-next/lib/mock/platformStatus.ts frontend-next/lib/mock/reportMetrics.ts
```

If the batch is a single commit, `git revert <batch-commit>` does all of the
above. Audit records in `backend/data/evidence_guard_audit/` are research
evidence: keep them, don't delete them as part of a rollback.
