"use client";

import { useState } from "react";
import { RefreshCw, Trash2 } from "lucide-react";

import type { KnowledgeDocument } from "@/lib/mock/documents";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DocumentRowProps {
  document: KnowledgeDocument;
  /** True while a delete or re-index call for this specific document is
   * in flight — drives per-row loading affordances. */
  pending: boolean;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

/**
 * A single Knowledge Base document row — collapsed by default (status,
 * chunk/vector counts, quick actions) and expandable via the native
 * `<details>`/`<summary>` disclosure for the full metadata viewer, matching
 * the keyboard/screen-reader-accessible pattern already established by
 * `components/answer/SourceCard.tsx`.
 */
export function DocumentRow({ document, pending, onDelete, onReindex }: DocumentRowProps) {
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const statusVariant =
    document.status === "Indexed"
      ? "kb-status-badge--ok"
      : document.status === "Indexing"
        ? "kb-status-badge--pending"
        : "kb-status-badge--failed";

  function handleDeleteClick() {
    if (!confirmingDelete) {
      setConfirmingDelete(true);
      return;
    }
    setConfirmingDelete(false);
    onDelete(document.id);
  }

  return (
    <details className="source-row kb-doc-row">
      <summary className="source-row-summary kb-doc-row-summary">
        <span className="kb-doc-row-name">{document.name}</span>

        <Badge variant="outline" className={cn("kb-status-badge", statusVariant)}>
          {document.status}
        </Badge>

        <span className="kb-doc-row-stat">{document.chunkCount} chunks</span>
        <span className="kb-doc-row-stat">{document.vectorCount} vectors</span>

        <span className="kb-doc-row-actions" onClick={(event) => event.preventDefault()}>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            disabled={pending}
            aria-label={`Re-index ${document.name}`}
            title="Re-index"
            onClick={() => onReindex(document.id)}
          >
            <RefreshCw
              size={14}
              className={cn(document.status === "Indexing" && "kb-spin-icon")}
              aria-hidden="true"
            />
          </Button>
          <Button
            type="button"
            variant={confirmingDelete ? "destructive" : "ghost"}
            size={confirmingDelete ? "sm" : "icon-sm"}
            disabled={pending}
            aria-label={
              confirmingDelete
                ? `Confirm delete ${document.name}`
                : `Delete ${document.name}`
            }
            title={confirmingDelete ? "Confirm delete" : "Delete"}
            onClick={handleDeleteClick}
            onBlur={() => setConfirmingDelete(false)}
          >
            <Trash2 size={14} aria-hidden="true" />
            {confirmingDelete && "Confirm"}
          </Button>
        </span>

        <span className="source-row-marker" aria-hidden="true" />
      </summary>

      <div className="source-row-body">
        <dl className="source-row-meta">
          <div className="source-row-meta-item">
            <dt>Category</dt>
            <dd>{document.category}</dd>
          </div>
          <div className="source-row-meta-item">
            <dt>File size</dt>
            <dd>{formatBytes(document.sizeBytes)}</dd>
          </div>
          <div className="source-row-meta-item">
            <dt>Embedding model</dt>
            <dd>{document.embeddingModel}</dd>
          </div>
          <div className="source-row-meta-item">
            <dt>Uploaded</dt>
            <dd>{formatDate(document.uploadedAt)}</dd>
          </div>
          <div className="source-row-meta-item">
            <dt>Chunk count</dt>
            <dd>{document.chunkCount}</dd>
          </div>
          <div className="source-row-meta-item">
            <dt>Vector count</dt>
            <dd>{document.vectorCount}</dd>
          </div>
        </dl>
      </div>
    </details>
  );
}
