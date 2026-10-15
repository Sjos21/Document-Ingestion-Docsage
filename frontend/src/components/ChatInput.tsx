import { useState } from "react";
import { Send } from "lucide-react";

export function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [value, setValue] = useState("");

  const submit = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="border-t border-border p-3 flex gap-2">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder="Ask a question about your documents..."
        className="flex-1 bg-transparent border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
      />
      <button
        onClick={submit}
        disabled={disabled}
        className="border border-border rounded-md px-3 flex items-center justify-center hover:border-accent disabled:opacity-40"
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  );
}