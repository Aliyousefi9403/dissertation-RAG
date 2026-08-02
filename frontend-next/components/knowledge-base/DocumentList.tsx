import type { KnowledgeDocument } from "@/lib/mock/documents";
import { DocumentRow } from "@/components/knowledge-base/DocumentRow";

interface DocumentListProps {
  documents: KnowledgeDocument[];
  pendingIds: Set<string>;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
  emptyMessage: string;
}

export function DocumentList({
  documents,
  pendingIds,
  onDelete,
  onReindex,
  emptyMessage,
}: DocumentListProps) {
  if (documents.length === 0) {
    return <p className="kb-empty">{emptyMessage}</p>;
  }

  return (
    <div className="source-list">
      {documents.map((document) => (
        <DocumentRow
          key={document.id}
          document={document}
          pending={pendingIds.has(document.id)}
          onDelete={onDelete}
          onReindex={onReindex}
        />
      ))}
    </div>
  );
}
