import { useDocuments } from "../hooks/useDocuments";
import { UploadDropzone } from "./UploadDropzone";
import { DocumentCard } from "./DocumentCard";

export function Sidebar() {
  const { documents, loading, upload, remove, updateStatus } = useDocuments();

  return (
    <aside className="w-72 border-r border-border p-4 flex flex-col gap-3 shrink-0 overflow-y-auto">
      <div className="text-xs text-muted uppercase tracking-wide">Documents</div>
      <UploadDropzone onUpload={upload} />
      <div className="flex flex-col gap-2">
        {loading && <div className="text-xs text-muted">Loading...</div>}
        {!loading && documents.length === 0 && (
          <div className="text-sm text-muted italic">No documents yet</div>
        )}
        {documents.map((doc) => (
          <DocumentCard key={doc.id} doc={doc} onStatusChange={updateStatus} onDelete={remove} />
        ))}
      </div>
    </aside>
  );
}