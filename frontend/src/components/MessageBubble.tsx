import { cn } from "../lib/utils";
import { SourceCard } from "./SourceCard";
import { TransparencyPanel } from "./TransparencyPanel";
import type { ChatMessage } from "../types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("max-w-[70%] rounded-md px-3 py-2 text-sm", isUser ? "bg-accent/15" : "border border-border")}>
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex flex-col gap-1">
            {message.sources.map((s) => (
              <SourceCard key={s.chunk_id} source={s} />
            ))}
          </div>
        )}
        {message.trace && <TransparencyPanel trace={message.trace} />}
      </div>
    </div>
  );
}