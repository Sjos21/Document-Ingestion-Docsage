
import { useDocuments } from "../hooks/useDocuments";
import { UploadDropzone } from "./UploadDropzone";
import { DocumentCard } from "./DocumentCard";

export function Sidebar() {
  const { documents, loading, upload, remove, updateStatus } = useDocuments();

  return (
    <aside className="w-72 shrink-0 overflow-y-auto border-r border-border bg-[#0B1020]/95 p-4 flex flex-col gap-5">
      <div className="flex items-center gap-3 px-1 pt-1">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-lg shadow-violet-950/40">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="h-6 w-6 text-white"
            aria-hidden="true"
          >
            <path d="M7 3.75h7l5 5v11.5H7a2 2 0 0 1-2-2v-12a2.5 2.5 0 0 1 2-2.5Z" />
            <path d="M14 4v5h5M8.5 13h7M8.5 16.5h7" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-tight text-white">DocSage</h2>
          <p className="text-xs text-slate-400">Document intelligence</p>
        </div>
      </div>

      <div className="h-px bg-border" />

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            Your documents
          </h3>
          <span className="rounded-full border border-border bg-white/5 px-2 py-0.5 text-xs text-slate-300">
            {documents.length}
          </span>
        </div>

        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-2 transition-colors hover:border-violet-500/60">
          <UploadDropzone onUpload={upload} />
        </div>
      </section>

      <section className="flex min-h-0 flex-col gap-3">
        <h3 className="px-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
          Library
        </h3>

        {loading && (
          <div className="flex items-center gap-2 rounded-xl bg-white/[0.03] p-3 text-sm text-slate-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-violet-400" />
            Loading documents…
          </div>
        )}

        {!loading && documents.length === 0 && (
          <div className="rounded-xl border border-border bg-white/[0.025] px-4 py-5 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 text-slate-400">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                className="h-5 w-5"
                aria-hidden="true"
              >
                <path d="M7 3.75h7l5 5v11.5H7a2 2 0 0 1-2-2v-12a2.5 2.5 0 0 1 2-2.5Z" />
                <path d="M14 4v5h5M8.5 13h7M8.5 16.5h4" />
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-300">Your library is empty</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Upload a document to start asking questions.
            </p>
          </div>
        )}

        <div className="flex flex-col gap-2">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              doc={doc}
              onStatusChange={updateStatus}
              onDelete={remove}
            />
          ))}
        </div>
      </section>

      <div className="mt-auto rounded-xl border border-violet-400/15 bg-gradient-to-br from-violet-500/10 to-indigo-500/5 p-3">
        <div className="mb-1 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-xs font-medium text-slate-200">Workspace ready</span>
        </div>
        <p className="text-xs leading-5 text-slate-500">
          Your documents stay organized in one searchable workspace.
        </p>
      </div>
    </aside>
  );
}
