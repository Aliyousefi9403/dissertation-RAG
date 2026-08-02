"use client";

import { Search } from "lucide-react";

interface DocumentSearchInputProps {
  value: string;
  onChange: (value: string) => void;
}

/** Search box for the Knowledge Base document list — filters by name or
 * category via `searchDocuments()` (see `lib/mock/documents.ts`). */
export function DocumentSearchInput({ value, onChange }: DocumentSearchInputProps) {
  return (
    <div className="kb-search">
      <Search aria-hidden="true" size={15} />
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search documents by name or category…"
        aria-label="Search knowledge base documents"
      />
    </div>
  );
}
