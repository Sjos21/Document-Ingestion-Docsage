import { FileText } from "lucide-react";
import type { SourceRef } from "../types";

export function SourceCard({ source }: { source: SourceRef }) {
  return (
    <div className="border border-border rounded px-2 py-1.5 text-[11px] flex items-center gap-1.5 min-w-0">
      <FileText className="h-3 w-3 text-muted shrink-0" />
      <span className="truncate">{source.filename}</span>
      <span className="text-muted font-mono shrink-0 ml-auto">
        {source.score.toFixed(2)}
      </span>
    </div>
  );
}