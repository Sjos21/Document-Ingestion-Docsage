
import { useEffect, useRef } from "react";
import { useChat } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

const suggestions = [
  {
    icon: "✦",
    title: "Summarize a document",
    description: "Get the main points in seconds.",
    prompt: "Summarize my uploaded document.",
  },
  {
    icon: "⌕",
    title: "Find key information",
    description: "Search for a fact or specific detail.",
    prompt: "What are the key points in my documents?",
  },
  {
    icon: "⇄",
    title: "Compare information",
    description: "Explore related details across content.",
    prompt: "Compare the main ideas in my documents.",
  },
  {
    icon: "☷",
    title: "Extract action items",
    description: "Identify decisions and next steps.",
    prompt: "List the important action items in my documents.",
  },
];

export function ChatArea() {
  const { messages, send, busy } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-transparent">
      <header className="flex h-[65px] shrink-0 items-center justify-between border-b border-border px-5 sm:px-8">
        <div>
          <h1 className="text-sm font-semibold text-slate-100">Workspace</h1>
          <p className="mt-0.5 text-xs text-slate-500">
            Your personal AI document assistant
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/[0.07] px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-xs font-medium text-emerald-300">Ready to chat</span>
        </div>
      </header>

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-6 sm:px-8">
        {messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center py-8">
            <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-violet-400/20 bg-gradient-to-br from-violet-500/20 to-indigo-500/10 shadow-lg shadow-violet-950/20">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="h-8 w-8 text-violet-300"
                aria-hidden="true"
              >
                <path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z" />
                <path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z" />
              </svg>
            </div>

            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-violet-300">
              Meet your document assistant
            </p>
            <h2 className="max-w-xl text-center text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Your documents.
              <span className="block bg-gradient-to-r from-violet-300 to-indigo-300 bg-clip-text text-transparent">
                A little more intelligent.
              </span>
            </h2>
            <p className="mt-4 max-w-lg text-center text-sm leading-6 text-slate-400 sm:text-base">
              Upload your files and ask questions in plain language. Find details,
              understand complex content, and get answers grounded in your documents.
            </p>

            <div className="mt-9 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
              {suggestions.map((item) => (
                <button
                  key={item.title}
                  type="button"
                  onClick={() => void send(item.prompt)}
                  disabled={busy}
                  className="group rounded-2xl border border-border bg-slate-900/50 p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-violet-400/40 hover:bg-violet-500/[0.06] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl border border-violet-400/15 bg-violet-500/10 text-lg text-violet-300 transition-colors group-hover:bg-violet-500/20">
                    {item.icon}
                  </div>
                  <p className="text-sm font-semibold text-slate-200">{item.title}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {item.description}
                  </p>
                </button>
              ))}
            </div>

            <p className="mt-6 text-xs text-slate-600">
              For best results, upload a document before asking a question.
            </p>
          </div>
        ) : (
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
            {messages.map((m, i) => (
              <MessageBubble key={i} message={m} />
            ))}
            {busy && (
              <div className="flex items-center gap-3 self-start rounded-xl border border-border bg-slate-900/70 px-4 py-3 text-sm text-slate-400">
                <span className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-400" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-400 [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-400 [animation-delay:240ms]" />
                </span>
                Thinking through your documents…
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-border bg-[#080B14]/90 px-4 pb-4 pt-3 sm:px-8">
        <div className="mx-auto w-full max-w-3xl">
          <div className="rounded-2xl border border-slate-700/80 bg-slate-900/80 p-1.5 shadow-lg shadow-black/10 transition-colors focus-within:border-violet-400/50 focus-within:ring-2 focus-within:ring-violet-500/10">
            <ChatInput onSend={send} disabled={busy} />
          </div>
          <p className="mt-2 text-center text-[11px] text-slate-600">
            AI-generated answers can be inaccurate. Verify important information against your sources.
          </p>
        </div>
      </div>
    </main>
  );
}
