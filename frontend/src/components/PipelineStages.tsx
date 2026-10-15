import { Check, Loader2 } from "lucide-react";
import { cn } from "../lib/utils";
import type { DocumentStatus } from "../types";

const STAGES: { key: DocumentStatus; label: string }[] = [
  { key: "uploaded", label: "Uploaded" },
  { key: "extracting", label: "Extracted" },
  { key: "chunking", label: "Chunked" },
  { key: "embedding", label: "Embedded" },
  { key: "indexing", label: "Indexed" },
];

export function PipelineStages({ status }: { status: DocumentStatus }) {
  if (status === "failed") {
    return <p className="text-xs text-red-500 mt-1">Processing failed</p>;
  }
  const currentIdx = STAGES.findIndex((s) => s.key === status);
  const doneIdx = status === "indexed" ? STAGES.length : currentIdx;

  return (
    <div className="flex flex-col gap-0.5 mt-1.5">
      {STAGES.map((stage, i) => {
        const isDone = i < doneIdx || status === "indexed";
        const isActive = i === currentIdx && status !== "indexed";
        return (
          <div key={stage.key} className="flex items-center gap-1.5 text-[11px]">
            {isDone ? (
              <Check className="h-3 w-3 text-accent shrink-0" />
            ) : isActive ? (
              <Loader2 className="h-3 w-3 text-accent shrink-0 animate-spin" />
            ) : (
              <div className="h-3 w-3 rounded-full border border-border shrink-0" />
            )}
            <span className={cn(isDone || isActive ? "text-fg" : "text-muted")}>{stage.label}</span>
          </div>
        );
      })}
    </div>
  );
}