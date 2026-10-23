import type { Metadata } from "next";

import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { T } from "@/components/T";
import { DEFAULT_LANG, DEFAULT_SCRIPT, PREFERENCES_SCRIPT } from "@/lib/preferences";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "TAMASHEQ", template: "%s · TAMASHEQ" },
  description:
    "Infrastructure linguistique et IA pour la langue tamasheq, gouvernée avec les communautés.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // Les attributs data-lang / data-script / lang sont ajustés par PREFERENCES_SCRIPT avant
    // l'hydratation, d'où suppressHydrationWarning sur <html>.
    <html
      lang={DEFAULT_LANG}
      data-lang={DEFAULT_LANG}
      data-script={DEFAULT_SCRIPT}
      className="h-full antialiased"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: PREFERENCES_SCRIPT }} />
      </head>
      <body className="flex min-h-full flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:rounded focus:bg-accent focus:px-3 focus:py-2 focus:text-on-accent"
        >
          <T fr="Aller au contenu" en="Skip to content" />
        </a>
        <SiteHeader />
        <main id="main" className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
