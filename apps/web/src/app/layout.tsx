import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClassLens — Multimodal Math Diagnostic Platform",
  description: "Transparent, evidence-grounded math reasoning diagnostics for Singapore classrooms",
  icons: {
    icon: "/logos/logo.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface-canvas font-sans text-ink-primary antialiased">
        {children}
      </body>
    </html>
  );
}
