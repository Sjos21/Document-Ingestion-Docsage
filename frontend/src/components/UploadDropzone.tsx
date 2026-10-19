// import { useRef, useState } from "react";
// import { Upload } from "lucide-react";
// import { cn } from "../lib/utils";

// export function UploadDropzone({ onUpload }: { onUpload: (file: File) => Promise<string> }) {
//   const [dragging, setDragging] = useState(false);
//   const [busy, setBusy] = useState(false);
//   const inputRef = useRef<HTMLInputElement>(null);

//   const handleFile = async (file: File) => {
//     setBusy(true);
//     try {
//       await onUpload(file);
//     } finally {
//       setBusy(false);
//     }
//   };

//   return (
//     <div
//       onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
//       onDragLeave={() => setDragging(false)}
//       onDrop={(e) => {
//         e.preventDefault();
//         setDragging(false);
//         const file = e.dataTransfer.files[0];
//         if (file) handleFile(file);
//       }}
//       onClick={() => inputRef.current?.click()}
//       className={cn(
//         "border border-dashed border-border rounded-md p-4 text-center cursor-pointer transition-colors",
//         dragging ? "border-accent bg-accent/5" : "hover:border-muted",
//       )}
//     >
//       <Upload className="mx-auto mb-1.5 h-4 w-4 text-muted" />
//       <p className="text-xs text-muted">
//         {busy ? "Uploading..." : "Drop PDF or click to upload"}
//       </p>
//       <input
//         ref={inputRef}
//         type="file"
//         accept=".pdf"
//         className="hidden"
//         onChange={(e) => {
//           const file = e.target.files?.[0];
//           if (file) handleFile(file);
//           e.target.value = "";
//         }}
//       />
//     </div>
//   );
// }


import { useRef, useState } from "react";
import { Upload, FileText, LoaderCircle, Sparkles } from "lucide-react";
import { cn } from "../lib/utils";

export function UploadDropzone({
  onUpload,
}: {
  onUpload: (file: File) => Promise<string>;
}) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }

    setError("");
    setBusy(true);

    try {
      await onUpload(file);
    } catch {
      setError("Upload failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={busy ? -1 : 0}
        aria-label="Upload a PDF document"
        aria-disabled={busy}
        onDragOver={(e) => {
          e.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
            setDragging(false);
          }
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (busy) return;

          const file = e.dataTransfer.files[0];
          if (file) void handleFile(file);
        }}
        onClick={() => {
          if (!busy) inputRef.current?.click();
        }}
        onKeyDown={(e) => {
          if (!busy && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        className={cn(
          "group relative flex flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed p-5 text-center transition-all duration-200",
          dragging
            ? "border-violet-400 bg-violet-500/10"
            : "border-slate-700 bg-slate-950/40 hover:border-violet-400/60 hover:bg-violet-500/[0.05]",
          busy ? "cursor-wait opacity-80" : "cursor-pointer",
        )}
      >
        <div
          className={cn(
            "mb-3 flex h-11 w-11 items-center justify-center rounded-xl border transition-all duration-200",
            dragging
              ? "scale-105 border-violet-400/40 bg-violet-500/20 text-violet-200"
              : "border-slate-700 bg-slate-800 text-slate-300 group-hover:border-violet-400/30 group-hover:bg-violet-500/10 group-hover:text-violet-300",
          )}
        >
          {busy ? (
            <LoaderCircle className="h-5 w-5 animate-spin" />
          ) : dragging ? (
            <FileText className="h-5 w-5" />
          ) : (
            <Upload className="h-5 w-5" />
          )}
        </div>

        <p className="text-xs font-semibold text-slate-200">
          {busy
            ? "Uploading document…"
            : dragging
              ? "Drop your PDF here"
              : "Upload a document"}
        </p>

        <p className="mt-1.5 text-[11px] leading-5 text-slate-500">
          {busy ? "Please wait while we process your file" : "Drag and drop or browse files"}
        </p>

        {!busy && (
          <span className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-violet-400/15 bg-violet-500/10 px-2.5 py-1 text-[10px] font-medium text-violet-300">
            <Sparkles className="h-3 w-3" />
            PDF documents
          </span>
        )}

        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          disabled={busy}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
            e.target.value = "";
          }}
        />
      </div>

      {error && (
        <p role="alert" className="mt-2 rounded-lg border border-red-400/15 bg-red-500/[0.06] px-3 py-2 text-xs leading-5 text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
