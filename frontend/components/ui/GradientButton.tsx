import Link from "next/link";
import { ComponentProps } from "react";

import { cn } from "@/lib/utils";

type GradientButtonProps = ComponentProps<typeof Link> & {
  variant?: "primary" | "secondary";
};

export function GradientButton({ className, variant = "primary", ...props }: GradientButtonProps) {
  return (
    <Link
      className={cn(
        "inline-flex min-h-12 items-center justify-center rounded-lg px-6 py-3 text-sm font-semibold transition duration-300 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-300/40",
        variant === "primary"
          ? "bg-gradient-to-r from-blue-500 via-violet-500 to-amber-400 text-white shadow-[0_16px_48px_rgba(96,165,250,0.36)] hover:shadow-[0_18px_58px_rgba(168,85,247,0.28)]"
          : "border border-white/40 bg-white/40 text-slate-800 shadow-[0_12px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl hover:bg-white/60",
        className
      )}
      {...props}
    />
  );
}
