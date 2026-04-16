"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { Providers } from "@/app/providers";
import ScreeningDueBanner from "@/components/ScreeningDueBanner";

const immersiveRoutes = new Set(["/"]);

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isImmersive = immersiveRoutes.has(pathname);

  return (
    <Providers>
      {!isImmersive ? <ScreeningDueBanner /> : null}
      <main className={isImmersive ? "min-h-screen" : "mx-auto max-w-6xl px-4 py-20"}>
        {children}
      </main>
    </Providers>
  );
}
