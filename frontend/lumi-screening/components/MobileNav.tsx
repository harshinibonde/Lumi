"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "../styles/mobile-nav.module.css";

const items = [
  { href: "/dashboard", label: "Home", icon: "home" },
  { href: "/chat", label: "Chat", icon: "forum" },
  { href: "/analytics", label: "Progress", icon: "analytics" },
  { href: "/settings", label: "Settings", icon: "settings" },
];

export default function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className={styles.bar}>
      {items.map((item) => {
        const active = pathname?.startsWith(item.href);
        return (
          <Link key={item.href} href={item.href} className={`${styles.btn} ${active ? styles.active : ""}`}>
            <span className="material-symbols-outlined">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
