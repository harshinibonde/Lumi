"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import Header from "./Header";
import Footer from "./Footer";

const publicRoutes = new Set(["/"]);

export default function LayoutChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isPublic = pathname ? publicRoutes.has(pathname) : false;

  return (
    <>
      {isPublic && <Header />}
      {children}
      {isPublic && <Footer />}
    </>
  );
}
