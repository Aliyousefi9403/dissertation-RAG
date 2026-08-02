"use client";

import { useEffect, useState } from "react";

import type { KnowledgeDocument } from "@/lib/mock/documents";
import {
  deleteDocument,
  listDocuments,
  reindexDocument,
  searchDocuments,
  uploadDocument,
} from "@/lib/mock/documents";
import { DocumentUpload } from "@/components/knowledge-base/DocumentUpload";
import { DocumentSearchInput } from "@/components/knowledge-base/DocumentSearchInput";
import { DocumentList } from "@/components/knowledge-base/DocumentList";

const SEARCH_DEBOUNCE_MS = 220;

type LoadState = "loading" | "ready" | "error";

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [query, setQuery] = useState("");
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());
  const [uploading, setUploading] = useState(false);

  // Initial load, and every debounced query change — `searchDocuments`
  // handles both the empty-query ("all documents") and filtered cases, so
  // this single effect covers load + search.
  useEffect(() => {
    let cancelled = false;

    const timeoutId = setTimeout(() => {
      if (cancelled) return;
      setLoadState((prev) => (prev === "ready" ? "ready" : "loading"));

      searchDocuments(query)
        .then((result) => {
          if (cancelled) return;
          setDocuments(result);
          setLoadState("ready");
        })
        .catch(() => {
          if (cancelled) return;
          setLoadState("error");
        });
    }, query ? SEARCH_DEBOUNCE_MS : 0);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [query]);

  async function refresh() {
    const result = await listDocuments();
    setDocuments(result);
  }

  function withPending(id: string, run: () => Promise<void>) {
    setPendingIds((prev) => new Set(prev).add(id));
    run().finally(() => {
      setPendingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    });
  }

  function handleDelete(id: string) {
    withPending(id, async () => {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    });
  }

  function handleReindex(id: string) {
    setDocuments((prev) =>
      prev.map((doc) => (doc.id === id ? { ...doc, status: "Indexing" } : doc)),
    );
    withPending(id, async () => {
      const updated = await reindexDocument(id);
      setDocuments((prev) => prev.map((doc) => (doc.id === id ? updated : doc)));
    });
  }

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      await uploadDocument(file);
      await refresh();
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="workspace">
      <header className="topbar">
        <div>
          <p className="eyebrow">Knowledge Base</p>
          <h2>Manage the documents AegisRAG retrieves from</h2>
        </div>
      </header>

      <div className="kb-content">
        <DocumentUpload onUpload={handleUpload} uploading={uploading} />

        <div className="kb-toolbar">
          <DocumentSearchInput value={query} onChange={setQuery} />
          {loadState === "ready" && (
            <span className="kb-count">
              {documents.length} {documents.length === 1 ? "document" : "documents"}
            </span>
          )}
        </div>

        {loadState === "loading" && (
          <p className="kb-empty" aria-live="polite">
            Loading knowledge base documents…
          </p>
        )}

        {loadState === "error" && (
          <p className="kb-empty kb-empty--error" role="alert">
            Could not load the knowledge base. Please try again.
          </p>
        )}

        {loadState === "ready" && (
          <DocumentList
            documents={documents}
            pendingIds={pendingIds}
            onDelete={handleDelete}
            onReindex={handleReindex}
            emptyMessage={
              query
                ? `No documents match "${query}".`
                : "No documents in the knowledge base yet."
            }
          />
        )}
      </div>
    </section>
  );
}
