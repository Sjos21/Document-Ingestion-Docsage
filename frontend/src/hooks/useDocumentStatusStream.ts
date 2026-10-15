import { useEffect } from "react";
import { BASE_URL } from "../lib/api";
import type { DocumentStatus } from "../types";

const TERMINAL: DocumentStatus[] = ["indexed", "failed"];

/** Opens an SSE connection for a single non-terminal document and calls
 * onStatus on every update, closing automatically once terminal. */
export function useDocumentStatusStream(
  id: string,
  status: DocumentStatus,
  token: string | null,
  onStatus: (status: DocumentStatus) => void,
) {
  useEffect(() => {
    if (!token || TERMINAL.includes(status)) return;

    const controller = new AbortController();
    (async () => {
      const res = await fetch(`${BASE_URL}/documents/${id}/status/stream`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      if (!res.body) return;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          const match = line.match(/^data: (.+)$/m);
          if (!match) continue;
          try {
            const payload = JSON.parse(match[1]);
            if (payload.status) onStatus(payload.status as DocumentStatus);
          } catch {
            /* ignore malformed frame */
          }
        }
      }
    })().catch(() => {});

    return () => controller.abort();
  }, [id, status, token, onStatus]);
}