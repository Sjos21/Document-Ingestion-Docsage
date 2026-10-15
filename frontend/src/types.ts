export type DocumentStatus =
  | "uploaded" | "extracting" | "chunking" | "embedding" | "indexing" | "indexed" | "failed";

export interface DocumentItem {
  id: string;
  filename: string;
  status: DocumentStatus;
  status_reason: string | null;
  indexed_at: string | null;
  created_at: string;
}

export interface SourceRef {
  chunk_id: string;
  document_id: string;
  filename: string;
  score: number;
}

export interface ChatTrace {
  vector_ms: number;
  bm25_ms: number;
  fusion_ms: number;
  rerank_ms: number;
  generation_ms: number;
  vector_count: number;
  bm25_count: number;
  fused_count: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceRef[];
  trace?: ChatTrace;
}