import Link from "next/link";
import Image from "next/image";
import styles from "../styles/footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <Image
            src="/Lumi_logo.png"
            alt="Lumi"
            width={24}
            height={24}
            className={styles.logoImg}
          />
          <span className={styles.word}>Lumi</span>
        </div>
        <nav className={styles.links}>
          <Link href="/#how-it-works">About</Link>
          <Link href="#">Privacy Policy</Link>
          <Link href="#">Contact Us</Link>
        </nav>
        <div className={styles.copy}>
          © {new Date().getFullYear()} Lumi Cognitive Health. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
