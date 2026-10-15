import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { ChatTrace } from "../types";

const ROWS: { key: keyof ChatTrace; label: string; isCount?: boolean }[] = [
  { key: "vector_count", label: "Vector candidates", isCount: true },
  { key: "vector_ms", label: "Vector search" },
  { key: "bm25_count", label: "BM25 candidates", isCount: true },
  { key: "bm25_ms", label: "BM25 search" },
  { key: "fused_count", label: "Fused candidates", isCount: true },
  { key: "fusion_ms", label: "RRF fusion" },
  { key: "rerank_ms", label: "Cross-encoder rerank" },
  { key: "generation_ms", label: "LLM generation" },
];

export function TransparencyPanel({ trace }: { trace: ChatTrace }) {
  const [open, setOpen] = useState(false);
  const totalMs = trace.vector_ms + trace.bm25_ms + trace.fusion_ms + trace.rerank_ms + trace.generation_ms;

  return (
    <div className="mt-2 border border-border rounded-md">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] text-muted hover:text-fg"
      >
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        How this answer was built
        <span className="ml-auto font-mono">{totalMs.toFixed(0)}ms total</span>
      </button>
      {open && (
        <div className="px-2.5 pb-2.5 flex flex-col gap-1 border-t border-border pt-2">
          {ROWS.map((row) => (
            <div key={row.key} className="flex items-center justify-between text-[11px]">
              <span className="text-muted">{row.label}</span>
              <span className="font-mono">
                {row.isCount ? trace[row.key] : `${(trace[row.key] as number).toFixed(1)}ms`}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}