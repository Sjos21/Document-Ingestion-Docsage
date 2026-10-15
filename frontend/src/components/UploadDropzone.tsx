import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "../lib/utils";

export function UploadDropzone({ onUpload }: { onUpload: (file: File) => Promise<string> }) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setBusy(true);
    try {
      await onUpload(file);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "border border-dashed border-border rounded-md p-4 text-center cursor-pointer transition-colors",
        dragging ? "border-accent bg-accent/5" : "hover:border-muted",
      )}
    >
      <Upload className="mx-auto mb-1.5 h-4 w-4 text-muted" />
      <p className="text-xs text-muted">
        {busy ? "Uploading..." : "Drop PDF or click to upload"}
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
    </div>
  );
}