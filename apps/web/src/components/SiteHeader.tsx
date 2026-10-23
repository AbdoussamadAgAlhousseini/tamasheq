"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { NAV } from "@/lib/modules";

import { Preferences } from "./Preferences";
import { T } from "./T";

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="border-b border-line">
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="text-lg font-semibold tracking-wide">
          TAMASHEQ
        </Link>
        <button
          type="button"
          className="rounded-md border border-line px-3 py-1.5 text-sm md:hidden"
          aria-expanded={open}
          aria-controls="site-nav"
          onClick={() => setOpen((o) => !o)}
        >
          Menu
        </button>
      </div>
      <div
        id="site-nav"
        className={`${open ? "block" : "hidden"} mx-auto max-w-3xl px-4 pb-3 md:block`}
      >
        <nav aria-label="Navigation principale / Main navigation">
          <ul className="flex flex-col gap-1 md:flex-row md:flex-wrap md:gap-x-5">
            {NAV.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={pathname === item.href ? "page" : undefined}
                  onClick={() => setOpen(false)}
                  className="block py-1.5 text-sm text-muted hover:text-foreground aria-[current=page]:font-semibold aria-[current=page]:text-foreground"
                >
                  <T fr={item.label.fr} en={item.label.en} />
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="mt-3">
          <Preferences />
        </div>
      </div>
    </header>
  );
}
