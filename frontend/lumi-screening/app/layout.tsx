import type { Metadata } from "next";
import { Newsreader, Manrope } from "next/font/google";
import "../styles/globals.css";
import LayoutChrome from "../components/LayoutChrome";
import { ToastProvider } from "../components/Toast";

const newsreader = Newsreader({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-headline",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Lumi — A Gentle Light for Your Mind",
  description:
    "Voice-first cognitive companion supporting memory recall and cognitive wellness. Fully local, always private.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${newsreader.variable} ${manrope.variable}`}>
        <ToastProvider>
          <LayoutChrome>{children}</LayoutChrome>
        </ToastProvider>
      </body>
    </html>
  );
}
