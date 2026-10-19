// import { cn } from "../lib/utils";
// import { SourceCard } from "./SourceCard";
// import { TransparencyPanel } from "./TransparencyPanel";
// import type { ChatMessage } from "../types";

// export function MessageBubble({ message }: { message: ChatMessage }) {
//   const isUser = message.role === "user";
//   return (
//     <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
//       <div className={cn("max-w-[70%] rounded-md px-3 py-2 text-sm", isUser ? "bg-accent/15" : "border border-border")}>
//         <p className="whitespace-pre-wrap">{message.content}</p>
//         {message.sources && message.sources.length > 0 && (
//           <div className="mt-2 flex flex-col gap-1">
//             {message.sources.map((s) => (
//               <SourceCard key={s.chunk_id} source={s} />
//             ))}
//           </div>
//         )}
//         {message.trace && <TransparencyPanel trace={message.trace} />}
//       </div>
//     </div>
//   );
// }


import { cn } from "../lib/utils";
import { SourceCard } from "./SourceCard";
import { TransparencyPanel } from "./TransparencyPanel";
import { Bot, UserRound, Sparkles } from "lucide-react";
import type { ChatMessage } from "../types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full items-start gap-3",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-violet-400/20 bg-violet-500/10 text-violet-300">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div
        className={cn(
          "min-w-0 max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-7 sm:max-w-[75%]",
          isUser
            ? "rounded-tr-md border border-violet-400/20 bg-violet-500/15 text-slate-100"
            : "rounded-tl-md border border-slate-700/80 bg-slate-900/75 text-slate-200 shadow-sm shadow-black/10",
        )}
      >
        {isUser && (
          <div className="mb-1.5 flex items-center justify-end gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-violet-300">
            <UserRound className="h-3 w-3" />
            You
          </div>
        )}

        {!isUser && (
          <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-violet-300">
            <Sparkles className="h-3 w-3" />
            DocSage AI
          </div>
        )}

        <p className="whitespace-pre-wrap break-words">{message.content}</p>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-4 border-t border-slate-700/70 pt-3">
            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Sources · {message.sources.length}
            </p>

            <div className="flex flex-col gap-2">
              {message.sources.map((source) => (
                <SourceCard key={source.chunk_id} source={source} />
              ))}
            </div>
          </div>
        )}

        {message.trace && (
          <div className="mt-3 border-t border-slate-700/70 pt-3">
            <TransparencyPanel trace={message.trace} />
          </div>
        )}
      </div>
    </div>
  );
}
