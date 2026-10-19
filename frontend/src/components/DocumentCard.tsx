// import { FileText, Trash2 } from "lucide-react";
// import { getAccessToken } from "../lib/api";
// import { useDocumentStatusStream } from "../hooks/useDocumentStatusStream";
// import { PipelineStages } from "./PipelineStages";
// import type { DocumentItem, DocumentStatus } from "../types";

// const TERMINAL: DocumentStatus[] = ["indexed", "failed"];

// export function DocumentCard({
//   doc, onStatusChange, onDelete,
// }: {
//   doc: DocumentItem;
//   onStatusChange: (id: string, status: DocumentStatus) => void;
//   onDelete: (id: string) => void;
// }) {
//   useDocumentStatusStream(doc.id, doc.status, getAccessToken(), (status) =>
//     onStatusChange(doc.id, status),
//   );

//   return (
//     <div className="border border-border rounded-md p-2.5 group">
//       <div className="flex items-start justify-between gap-2">
//         <div className="flex items-center gap-1.5 min-w-0">
//           <FileText className="h-3.5 w-3.5 text-muted shrink-0" />
//           <span className="text-xs truncate">{doc.filename}</span>
//         </div>
//         <button
//           onClick={() => onDelete(doc.id)}
//           className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
//         >
//           <Trash2 className="h-3.5 w-3.5 text-muted hover:text-red-500" />
//         </button>
//       </div>
//       {!TERMINAL.includes(doc.status) && <PipelineStages status={doc.status} />}
//       {doc.status === "indexed" && <p className="text-[11px] text-muted mt-1">Ready</p>}
//       {doc.status === "failed" && <PipelineStages status={doc.status} />}
//     </div>
//   );
// }


import { FileText, Trash2, CheckCircle2, AlertCircle, LoaderCircle } from "lucide-react";
import { getAccessToken } from "../lib/api";
import { useDocumentStatusStream } from "../hooks/useDocumentStatusStream";
import { PipelineStages } from "./PipelineStages";
import type { DocumentItem, DocumentStatus } from "../types";

const TERMINAL: DocumentStatus[] = ["indexed", "failed"];

export function DocumentCard({
  doc,
  onStatusChange,
  onDelete,
}: {
  doc: DocumentItem;
  onStatusChange: (id: string, status: DocumentStatus) => void;
  onDelete: (id: string) => void;
}) {
  useDocumentStatusStream(doc.id, doc.status, getAccessToken(), (status) =>
    onStatusChange(doc.id, status),
  );

  const indexed = doc.status === "indexed";
  const failed = doc.status === "failed";
  const processing = !TERMINAL.includes(doc.status);

  return (
    <div className="group rounded-xl border border-border bg-slate-900/50 p-3 transition-all duration-200 hover:border-slate-600 hover:bg-slate-800/60">
      <div className="flex min-w-0 items-start gap-2.5">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
            indexed
              ? "border-emerald-400/15 bg-emerald-500/10 text-emerald-300"
              : failed
                ? "border-red-400/15 bg-red-500/10 text-red-300"
                : "border-violet-400/15 bg-violet-500/10 text-violet-300"
          }`}
        >
          <FileText className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1 pt-0.5">
          <p title={doc.filename} className="truncate text-xs font-medium leading-5 text-slate-200">
            {doc.filename}
          </p>

          <div className="mt-1.5 flex items-center gap-1.5">
            {indexed && (
              <>
                <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                <span className="text-[11px] font-medium text-emerald-300">Indexed and ready</span>
              </>
            )}

            {failed && (
              <>
                <AlertCircle className="h-3 w-3 text-red-400" />
                <span className="text-[11px] font-medium text-red-300">Processing failed</span>
              </>
            )}

            {processing && (
              <>
                <LoaderCircle className="h-3 w-3 animate-spin text-violet-300" />
                <span className="text-[11px] text-violet-200">Processing</span>
              </>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={() => onDelete(doc.id)}
          aria-label={`Delete ${doc.filename}`}
          title="Delete document"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-500 opacity-70 transition-all hover:bg-red-500/10 hover:text-red-300 focus-visible:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {processing && (
        <div className="mt-2.5 border-t border-border/70 pt-2">
          <PipelineStages status={doc.status} />
        </div>
      )}

      {failed && (
        <div className="mt-2.5 border-t border-red-400/10 pt-2">
          <PipelineStages status={doc.status} />
        </div>
      )}
    </div>
  );
}
