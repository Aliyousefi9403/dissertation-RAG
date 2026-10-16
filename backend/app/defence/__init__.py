"""
Experimental evidence-checking layer (detection batch 1).

This package adds a separate, opt-in `/guarded-chat` route that drafts an
answer with the unchanged baseline RAG pipeline and then checks the draft's
claims against the retrieved evidence with a second, independent model call.

It is an *experimental evidence-support baseline*, not a validated poison
detector: a poisoned source can "support" a false answer. It never touches
the existing `defended` collection, `/chat`, `/compare` or any corpus.
"""
