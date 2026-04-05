"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import styles from "../styles/sidebar.module.css";
import { getState, resetState } from "../lib/state";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: "home" },
  { href: "/chat", label: "Chat", icon: "forum" },
  { href: "/analytics", label: "Analytics", icon: "analytics" },
  { href: "/settings", label: "Settings", icon: "settings" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const s = getState();
  const initials = (s.userName || "Guest")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((x) => x[0]?.toUpperCase() ?? "")
    .join("") || "U";

  return (
    <aside className={styles.side}>
      {/* Brand */}
      <div className={styles.brand}>
        <Image src="/Lumi_logo.png" alt="Lumi" width={28} height={28} className={styles.brandLogo} />
        <div>
          <h1 className={styles.title}>The Journal</h1>
          <p className={styles.subtitle}>Your cognitive sanctuary</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className={styles.nav}>
        {items.map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.link} ${active ? styles.active : ""}`}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom area */}
      <div className={styles.bottom}>
        <Link href="/chat" className={styles.recordBtn}>
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>mic</span>
          <span>Record Memory</span>
        </Link>

        <div className={styles.userArea}>
          <div className={styles.avatar}>{initials}</div>
          <div className={styles.userInfo}>
            <div className={styles.userName}>{s.userName || "Guest"}</div>
            <button
              className={styles.logout}
              onClick={() => {
                resetState();
                router.push("/login");
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
