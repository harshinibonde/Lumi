import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function GlassCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/20 bg-white/30 shadow-[0_24px_80px_rgba(59,130,246,0.14)] backdrop-blur-xl",
        className
      )}
      {...props}
    />
  );
}
