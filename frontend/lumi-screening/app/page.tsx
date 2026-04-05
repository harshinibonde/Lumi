import Image from "next/image";
import Link from "next/link";
import styles from "../styles/landing.module.css";

export default function LandingPage() {
  return (
    <main>
      {/* ─── Hero ─────────────────────────────────────────────── */}
      <section className={styles.hero}>
        <div className={styles.heroBg}>
          <Image
            src="/landing-hero.jpg"
            alt="Caring interaction"
            fill
            priority
            className={styles.heroBgImg}
          />
          <div className={styles.heroOverlay} />
        </div>
        <div className={`${styles.heroContent} container`}>
          <div className={styles.heroBody}>
            <h1 className={`${styles.heroTitle} reveal reveal-1`}>
              Lighting the path <br /> to clearer memories
            </h1>
            <div className={`${styles.heroBtns} reveal reveal-2`}>
              <Link href="/login" className={`btn btn--primary btn--lg btn--pill ${styles.heroBtn}`}>
                Start Cognitive Check
              </Link>
              <Link href="/#how-it-works" className={`btn btn--surface btn--lg btn--pill ${styles.heroBtn}`}>
                Learn How Lumi Works
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ─── How It Works ─────────────────────────────────────── */}
      <section id="how-it-works" className={styles.section}>
        <div className="container">
          <div className={styles.sectionHead}>
            <div>
              <span className="sectionLabel">Methodology</span>
              <h2 className={styles.sectionTitle}>The Science of Softness</h2>
            </div>
          </div>
          <div className={styles.cardGrid}>
            <article className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <span className="material-symbols-outlined">psychology_alt</span>
              </div>
              <h3>Cognitive Screening</h3>
              <p>
                Inspired by clinical standards like MMSE and MoCA, reimagined for
                a dignified digital experience.
              </p>
            </article>
            <article className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <span className="material-symbols-outlined">analytics</span>
              </div>
              <h3>AI Cognitive Analysis</h3>
              <p>
                ML models analyze responses and memory recall to detect subtle
                cognitive patterns over time.
              </p>
            </article>
            <article className={styles.featureCard}>
              <div className={styles.featureIcon}>
                <span className="material-symbols-outlined">forum</span>
              </div>
              <h3>AI Cognitive Companion</h3>
              <p>
                Keeping minds active through supportive, natural AI conversations
                designed to engage and reassure.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* ─── Screening Interface ──────────────────────────────── */}
      <section className={styles.sectionAlt}>
        <div className="container">
          <div className={styles.splitRow}>
            <div className={styles.splitVisual}>
              <div className={styles.haloWrap}>
                <div className="luminousHalo" style={{ top: '-20%', left: '-20%' }} />
              </div>
              <div className={styles.screeningCard}>
                <div className={styles.screeningHeader}>
                  <span className={styles.screeningLabel}>Screening Progress: Part 1 of 3</span>
                  <div className={styles.progressDots}>
                    <span className={styles.dotFilled} />
                    <span className={styles.dotEmpty} />
                    <span className={styles.dotEmpty} />
                  </div>
                </div>
                <h4 className={styles.screeningQ}>
                  &ldquo;Can you please identify the year, the season, and the
                  day of the week?&rdquo;
                </h4>
                <div className={styles.screeningOptions}>
                  <div className={styles.screeningOption}>
                    <span>Speak Response</span>
                    <span className="material-symbols-outlined">mic</span>
                  </div>
                  <div className={styles.screeningOption}>
                    <span>Type Response</span>
                    <span className="material-symbols-outlined">keyboard</span>
                  </div>
                </div>
                <p className={styles.screeningNote}>
                  <span className="material-symbols-outlined" style={{ fontSize: 14 }}>info</span>
                  Response analysis is encrypted and private.
                </p>
              </div>
            </div>
            <div className={styles.splitText}>
              <span className="sectionLabel">Screening Interface</span>
              <h2 className={styles.sectionTitle}>
                Designed for Accessibility and Dignity
              </h2>
              <p className={styles.splitDesc}>
                Our screening module is built specifically for older adults. Large
                typefaces, voice support, and high-contrast elements ensure the
                process is stress-free and accurate.
              </p>
              <ul className={styles.checkList}>
                <li>
                  <span className="material-symbols-outlined">check_circle</span>
                  Clinically validated screening protocols
                </li>
                <li>
                  <span className="material-symbols-outlined">check_circle</span>
                  Adaptive difficulty based on user responses
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ─── AI Support (Dark Section) ────────────────────────── */}
      <section id="ai-support" className={styles.darkSection}>
        <div className={styles.darkGlow} />
        <div className="container">
          <div className={styles.splitRow}>
            <div className={styles.darkText}>
              <h2 className={styles.darkTitle}>
                Always There, <br /> Always Remembering
              </h2>
              <p className={styles.darkDesc}>
                Lumi AI isn&apos;t just a chatbot; it&apos;s a memory companion. It
                uses personal context to gently prompt recall and provide safe
                conversation at any hour.
              </p>
              <div className={styles.chatPreview}>
                <div className={styles.chatBubbleAI}>
                  <div className={styles.chatAvatar}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>auto_awesome</span>
                  </div>
                  <div className={styles.chatMsg}>
                    &ldquo;Good morning, Arthur. Would you like to tell me more
                    about that trip to the coast you mentioned yesterday?&rdquo;
                  </div>
                </div>
                <div className={styles.chatBubbleUser}>
                  <div className={styles.chatMsgUser}>
                    &ldquo;Yes, it was in 1974. The lighthouse had a very bright
                    red roof...&rdquo;
                  </div>
                  <div className={styles.chatAvatarUser}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>person</span>
                  </div>
                </div>
              </div>
            </div>
            <div className={styles.darkCards}>
              <div className={styles.darkCard}>
                <h4>Memory Anchors</h4>
                <p>Stores names and places to reinforce daily recall through conversation.</p>
              </div>
              <div className={styles.darkCard}>
                <h4>Adaptive Pace</h4>
                <p>Adjusts conversation complexity based on user responses and engagement.</p>
              </div>
              <div className={styles.darkCard}>
                <h4>Mood Awareness</h4>
                <p>Analyzes tone and sentiment to provide emotional support when needed.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Caregiver Tools ──────────────────────────────────── */}
      <section id="caregiver-tools" className={styles.sectionContainer}>
        <div className="container">
          <div className={styles.sectionCenter}>
            <span className="sectionLabel">Caregiver Ecosystem</span>
            <h2 className={styles.sectionTitle}>Tools for Connection</h2>
          </div>
          <div className={styles.caregiverGrid}>
            <div className={styles.dashCard}>
              <div className={styles.dashCardHeader}>
                <div>
                  <h3>Weekly Cognitive Engagement</h3>
                  <p>Track session activity and patterns</p>
                </div>
                <span className="material-symbols-outlined" style={{ color: 'var(--secondary)' }}>trending_up</span>
              </div>
              <div className={styles.barChart}>
                {[66, 50, 75, 83, 100, 66, 75].map((h, i) => (
                  <div key={i} className={styles.bar} style={{ height: `${h}%`, background: i === 4 ? 'var(--secondary)' : 'var(--primary-container)' }} />
                ))}
              </div>
              <div className={styles.dashStats}>
                <div>
                  <span>Alert Level</span>
                  <strong style={{ color: '#2f6d47' }}>Stable</strong>
                </div>
                <div>
                  <span>Conversations</span>
                  <strong>24 Sessions</strong>
                </div>
                <div>
                  <span>Recall Accuracy</span>
                  <strong>82%</strong>
                </div>
              </div>
            </div>
            <div className={styles.memoryVault}>
              <div className={styles.vaultImageWrap}>
                <div className={styles.vaultGradient} />
              </div>
              <div className={styles.vaultContent}>
                <h3>The Memory Vault</h3>
                <p>Add voice notes and stories for Lumi to weave into daily AI conversations.</p>
                <Link href="/login" className={styles.vaultBtn}>+ Add Memory</Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Mission Statement ────────────────────────────────── */}
      <section className={styles.sectionAlt}>
        <div className="container">
          <blockquote className={styles.mission}>
            &ldquo;Our mission is to ensure that no one has to walk the path of
            cognitive change in the dark.&rdquo;
          </blockquote>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────────────── */}
      <section className={styles.ctaSection}>
        <div className="container">
          <div className={styles.ctaCard}>
            <div className="luminousHalo" style={{ position: 'absolute', top: '-96px', left: '-96px', opacity: 0.3 }} />
            <div className={styles.ctaInner}>
              <h2 className={styles.ctaTitle}>Start Your Cognitive Check</h2>
              <p className={styles.ctaDesc}>
                Take the first step toward understanding and support. Our gentle
                screening takes only 15 minutes.
              </p>
              <Link href="/login" className={`btn btn--secondary btn--lg btn--pill`}>
                Begin Screening
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
