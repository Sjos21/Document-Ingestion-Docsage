// import { useState } from "react";
// import { Send } from "lucide-react";

// export function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
//   const [value, setValue] = useState("");

//   const submit = () => {
//     if (!value.trim() || disabled) return;
//     onSend(value.trim());
//     setValue("");
//   };

//   return (
//     <div className="border-t border-border p-3 flex gap-2">
//       <input
//         value={value}
//         onChange={(e) => setValue(e.target.value)}
//         onKeyDown={(e) => e.key === "Enter" && submit()}
//         placeholder="Ask a question about your documents..."
//         className="flex-1 bg-transparent border border-border rounded-md px-3 py-2 text-sm outline-none focus:border-accent"
//       />
//       <button
//         onClick={submit}
//         disabled={disabled}
//         className="border border-border rounded-md px-3 flex items-center justify-center hover:border-accent disabled:opacity-40"
//       >
//         <Send className="h-4 w-4" />
//       </button>
//     </div>
//   );
// }


import { useState } from "react";
import { Send, LoaderCircle, CornerDownLeft, Sparkles } from "lucide-react";

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;

    onSend(text);
    setValue("");
  };

  return (
    <div className="border-t border-slate-800/80 bg-[#080B14]/90 px-4 pb-4 pt-3 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <div className="group rounded-2xl border border-slate-700/80 bg-slate-900/80 shadow-lg shadow-black/10 transition-all duration-200 focus-within:border-violet-400/50 focus-within:shadow-violet-950/20">
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Ask anything about your documents..."
            aria-label="Message DocSage"
            disabled={disabled}
            rows={2}
            className="block max-h-40 min-h-14 w-full resize-y bg-transparent px-4 pb-2 pt-4 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-500 disabled:cursor-not-allowed"
          />

          <div className="flex items-center justify-between gap-3 px-3 pb-3">
            <div className="flex min-w-0 items-center gap-2 pl-1 text-[11px] text-slate-500">
              <Sparkles className="h-3.5 w-3.5 shrink-0 text-violet-400" />
              <span className="truncate">
                {disabled
                  ? "DocSage is thinking..."
                  : "Answers grounded in your documents"}
              </span>
            </div>

            <button
              type="button"
              onClick={submit}
              disabled={disabled || !value.trim()}
              aria-label={disabled ? "Generating response" : "Send message"}
              title="Send message"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-white shadow-md shadow-violet-950/30 transition-all hover:bg-violet-500 active:scale-95 disabled:cursor-not-allowed disabled:bg-slate-800 disabled:text-slate-500 disabled:shadow-none"
            >
              {disabled ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-[10px] text-slate-600">
          <CornerDownLeft className="h-3 w-3" />
          Enter to send · Shift + Enter for a new line
        </p>
      </div>
    </div>
  );
}
