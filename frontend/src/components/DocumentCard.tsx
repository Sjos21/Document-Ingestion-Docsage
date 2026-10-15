import { FileText, Trash2 } from "lucide-react";
import { getAccessToken } from "../lib/api";
import { useDocumentStatusStream } from "../hooks/useDocumentStatusStream";
import { PipelineStages } from "./PipelineStages";
import type { DocumentItem, DocumentStatus } from "../types";

const TERMINAL: DocumentStatus[] = ["indexed", "failed"];

export function DocumentCard({
  doc, onStatusChange, onDelete,
}: {
  doc: DocumentItem;
  onStatusChange: (id: string, status: DocumentStatus) => void;
  onDelete: (id: string) => void;
}) {
  useDocumentStatusStream(doc.id, doc.status, getAccessToken(), (status) =>
    onStatusChange(doc.id, status),
  );

  return (
    <div className="border border-border rounded-md p-2.5 group">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <FileText className="h-3.5 w-3.5 text-muted shrink-0" />
          <span className="text-xs truncate">{doc.filename}</span>
        </div>
        <button
          onClick={() => onDelete(doc.id)}
          className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
        >
          <Trash2 className="h-3.5 w-3.5 text-muted hover:text-red-500" />
        </button>
      </div>
      {!TERMINAL.includes(doc.status) && <PipelineStages status={doc.status} />}
      {doc.status === "indexed" && <p className="text-[11px] text-muted mt-1">Ready</p>}
      {doc.status === "failed" && <PipelineStages status={doc.status} />}
    </div>
  );
}