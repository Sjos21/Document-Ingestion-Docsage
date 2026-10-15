import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import type { DocumentItem } from "../types";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const res = await apiFetch("/documents");
    const data = await res.json();
    setDocuments(data.items);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const upload = useCallback(async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiFetch("/documents/upload", { method: "POST", body: formData });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    await refresh();
    return (await res.json()).id as string;
  }, [refresh]);

  const remove = useCallback(async (id: string) => {
    await apiFetch(`/documents/${id}`, { method: "DELETE" });
    await refresh();
  }, [refresh]);

  const updateStatus = useCallback((id: string, status: DocumentItem["status"]) => {
    setDocuments((prev) => prev.map((d) => (d.id === id ? { ...d, status } : d)));
  }, []);

  return { documents, loading, upload, remove, updateStatus, refresh };
}