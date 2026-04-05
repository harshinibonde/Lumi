"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import styles from "../styles/header.module.css";

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onDoc = (event: MouseEvent) => {
      if (!open || !wrapRef.current) return;
      if (!wrapRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ""}`}>
      <div className={`${styles.inner}`} ref={wrapRef}>
        {/* Logo */}
        <Link className={styles.logo} href="/" onClick={() => setOpen(false)}>
          <Image
            src="/Lumi_logo.png"
            alt="Lumi Logo"
            width={32}
            height={32}
            className={styles.logoImg}
          />
          <span className={styles.word}>Lumi</span>
        </Link>

        {/* Desktop Nav */}
        <nav className={styles.nav}>
          <Link href="/">Home</Link>
          <Link href="/#how-it-works">How It Works</Link>
          <Link href="/chat">LumiAI</Link>
          <Link href="/#caregiver-tools">Caregiver Tools</Link>
        </nav>

        {/* Actions */}
        <div className={styles.actions}>
          <Link href="/login" className={`btn btn--surface btn--pill ${styles.signIn}`}>
            Sign In / Login
          </Link>
          <button
            className={styles.menuBtn}
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            <span className="material-symbols-outlined">
              {open ? "close" : "menu"}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className={styles.mobileDrop}>
          <Link href="/" onClick={() => setOpen(false)}>Home</Link>
          <Link href="/#how-it-works" onClick={() => setOpen(false)}>How It Works</Link>
          <Link href="/#ai-support" onClick={() => setOpen(false)}>LumiAI</Link>
          <Link href="/#caregiver-tools" onClick={() => setOpen(false)}>Caregiver Tools</Link>
          <Link href="/login" onClick={() => setOpen(false)} className={styles.mobileSignIn}>
            Sign In / Login
          </Link>
        </div>
      )}
    </header>
  );
}
