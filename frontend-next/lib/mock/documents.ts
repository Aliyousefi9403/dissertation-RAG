/**
 * Mock Knowledge Base document store.
 *
 * No backend endpoint exists yet for document management — the real
 * backend only exposes `GET /health` and `POST /chat` (see
 * `backend/app/main.py`). This module fakes a small, realistic
 * cybersecurity-themed document set behind the same typed-async-function
 * shape a real API client would have (`listDocuments`, `searchDocuments`,
 * `deleteDocument`, `reindexDocument`, `uploadDocument`), so swapping to a
 * real `lib/api/documents.ts` later (once e.g. `GET/POST/DELETE
 * /api/documents` exist) only touches this file.
 *
 * State is kept in a module-level array so the Knowledge Base page behaves
 * like a real, stateful client against a (fake) backend across
 * upload/delete/reindex/search actions within a session — it intentionally
 * does not persist across a full page reload.
 *
 * Placeholder pending a real backend endpoint — swap this implementation
 * for real fetch() calls once document-management endpoints exist.
 */

export type DocumentStatus = "Indexed" | "Indexing" | "Failed";

export interface KnowledgeDocument {
  id: string;
  name: string;
  category: string;
  sizeBytes: number;
  chunkCount: number;
  vectorCount: number;
  /** Matches the real `EMBEDDING_MODEL` in `backend/app/config.py`. */
  embeddingModel: string;
  status: DocumentStatus;
  uploadedAt: string;
}

const EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2";

let documents: KnowledgeDocument[] = [
  {
    id: "doc-1",
    name: "owasp-top-10-2023.pdf",
    category: "Web Application Security",
    sizeBytes: 842_112,
    chunkCount: 138,
    vectorCount: 138,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexed",
    uploadedAt: "2026-06-02T09:14:00Z",
  },
  {
    id: "doc-2",
    name: "mitre-attack-enterprise-matrix.md",
    category: "Threat Intelligence",
    sizeBytes: 1_204_558,
    chunkCount: 264,
    vectorCount: 264,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexed",
    uploadedAt: "2026-06-04T14:02:00Z",
  },
  {
    id: "doc-3",
    name: "nist-sp-800-53-controls.txt",
    category: "Compliance & Governance",
    sizeBytes: 2_881_004,
    chunkCount: 501,
    vectorCount: 501,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexed",
    uploadedAt: "2026-06-10T11:47:00Z",
  },
  {
    id: "doc-4",
    name: "buffer-overflow-exploitation-notes.md",
    category: "Vulnerability Research",
    sizeBytes: 96_302,
    chunkCount: 21,
    vectorCount: 21,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexed",
    uploadedAt: "2026-06-14T08:30:00Z",
  },
  {
    id: "doc-5",
    name: "sql-injection-prevention-guide.pdf",
    category: "Secure Development",
    sizeBytes: 431_990,
    chunkCount: 74,
    vectorCount: 74,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexing",
    uploadedAt: "2026-07-22T16:05:00Z",
  },
  {
    id: "doc-6",
    name: "ransomware-incident-response-playbook.docx",
    category: "Incident Response",
    sizeBytes: 655_221,
    chunkCount: 112,
    vectorCount: 112,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexed",
    uploadedAt: "2026-07-05T10:18:00Z",
  },
  {
    id: "doc-7",
    name: "adversarial-poisoning-rag-pipelines.pdf",
    category: "AI / ML Security",
    sizeBytes: 1_012_776,
    chunkCount: 187,
    vectorCount: 187,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexed",
    uploadedAt: "2026-07-18T13:52:00Z",
  },
  {
    id: "doc-8",
    name: "ddos-mitigation-strategies.txt",
    category: "Network Security",
    sizeBytes: 210_445,
    chunkCount: 38,
    vectorCount: 0,
    embeddingModel: EMBEDDING_MODEL,
    status: "Failed",
    uploadedAt: "2026-07-29T07:41:00Z",
  },
];

const MOCK_LATENCY_MS = 220;

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

function cloneAll(): KnowledgeDocument[] {
  return documents.map((doc) => ({ ...doc }));
}

export async function listDocuments(): Promise<KnowledgeDocument[]> {
  return delay(cloneAll());
}

export async function searchDocuments(query: string): Promise<KnowledgeDocument[]> {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) {
    return delay(cloneAll());
  }
  const filtered = documents.filter(
    (doc) =>
      doc.name.toLowerCase().includes(trimmed) ||
      doc.category.toLowerCase().includes(trimmed),
  );
  return delay(filtered.map((doc) => ({ ...doc })));
}

export async function deleteDocument(id: string): Promise<void> {
  documents = documents.filter((doc) => doc.id !== id);
  return delay(undefined);
}

export async function reindexDocument(id: string): Promise<KnowledgeDocument> {
  documents = documents.map((doc) =>
    doc.id === id ? { ...doc, status: "Indexing" } : doc,
  );
  await delay(undefined, 900);

  documents = documents.map((doc) =>
    doc.id === id
      ? {
          ...doc,
          status: "Indexed",
          vectorCount: doc.chunkCount,
        }
      : doc,
  );

  const updated = documents.find((doc) => doc.id === id);
  if (!updated) {
    throw new Error(`Document ${id} not found.`);
  }
  return { ...updated };
}

export async function uploadDocument(file: File): Promise<KnowledgeDocument> {
  const estimatedChunks = Math.max(1, Math.round(file.size / 3200));
  const newDoc: KnowledgeDocument = {
    id: `doc-${Date.now()}`,
    name: file.name,
    category: "Uncategorised",
    sizeBytes: file.size,
    chunkCount: estimatedChunks,
    vectorCount: 0,
    embeddingModel: EMBEDDING_MODEL,
    status: "Indexing",
    uploadedAt: new Date().toISOString(),
  };

  documents = [newDoc, ...documents];
  await delay(undefined, 900);

  documents = documents.map((doc) =>
    doc.id === newDoc.id
      ? { ...doc, status: "Indexed", vectorCount: doc.chunkCount }
      : doc,
  );

  const updated = documents.find((doc) => doc.id === newDoc.id);
  return { ...(updated ?? newDoc) };
}
