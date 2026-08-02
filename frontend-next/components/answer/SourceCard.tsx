import type { SourceItem } from "@/lib/types/chat";
import { Markdown } from "@/components/answer/Markdown";

interface SourceCardProps {
  source: SourceItem;
}

function fileNameFromPath(path: string): string {
  const segments = path.split("/");
  return segments.at(-1) || path;
}

/**
 * `source.metadata` mirrors whatever the retriever/vector store attaches
 * to a chunk verbatim (see `backend/app/ingestion/load_documents.py`) —
 * it is not curated for display. Alongside genuinely user-facing fields
 * (e.g. `attack_type`, `origin`), it carries local filesystem paths
 * (`source`, duplicating the top-level `source.source` already shown as
 * a filename above) and internal pipeline/vector-store bookkeeping
 * (`source_authority`, `_id`, `_collection_name`, `start_index`) that
 * leak implementation/OS details and mean nothing to an end user. Only
 * an explicit allowlist of real, stable, user-meaningful keys is shown.
 */
const VISIBLE_METADATA_KEYS = new Set(["attack_type", "origin"]);

function formatMetadataValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

/**
 * A single retrieved-evidence row. Collapsed by default — showing only the
 * source number (matching the 3D shield-core's numbered nodes and the
 * static fallback's <ul>), filename and similarity score — and expandable
 * via the native <details>/<summary> disclosure, so it is fully keyboard-
 * and screen-reader-operable without any extra scripting.
 */
export function SourceCard({ source }: SourceCardProps) {
  const metadataEntries = Object.entries(source.metadata).filter(([key]) =>
    VISIBLE_METADATA_KEYS.has(key),
  );

  return (
    <details className="source-row">
      <summary className="source-row-summary">
        <span className="source-row-number" aria-hidden="true">
          {source.source_number}
        </span>
        <span className="source-row-name">{fileNameFromPath(source.source)}</span>
        <span className="source-row-score">
          similarity score <strong>{source.score.toFixed(4)}</strong>
        </span>
        <span className="source-row-marker" aria-hidden="true" />
      </summary>

      <div className="source-row-body">
        <div className="source-row-content">
          <Markdown content={source.content} />
        </div>

        {metadataEntries.length > 0 && (
          <dl className="source-row-meta">
            {metadataEntries.map(([key, value]) => (
              <div className="source-row-meta-item" key={key}>
                <dt>{key}</dt>
                <dd>{formatMetadataValue(value)}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </details>
  );
}
