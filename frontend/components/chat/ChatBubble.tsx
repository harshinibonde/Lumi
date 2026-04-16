import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type ChatBubbleProps = {
  role: "assistant" | "user";
  children: ReactNode;
};

export function ChatBubble({ role, children }: ChatBubbleProps) {
  const isAssistant = role === "assistant";

  return (
    <div
      className={cn(
        "rounded-2xl border p-4 text-sm leading-6 shadow-sm backdrop-blur-xl",
        isAssistant
          ? "border-blue-100/60 bg-blue-50/70 text-slate-800"
          : "border-white/50 bg-white/60 text-slate-800"
      )}
    >
      {children}
    </div>
  );
}
