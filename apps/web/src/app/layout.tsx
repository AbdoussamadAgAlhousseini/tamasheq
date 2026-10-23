import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TAMASHEQ",
  description:
    "Infrastructure linguistique et IA pour la langue tamasheq, gouvernée avec les communautés.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
