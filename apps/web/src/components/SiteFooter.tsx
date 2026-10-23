import Link from "next/link";

import { T } from "./T";

const REPO = "https://github.com/AbdoussamadAgAlhousseini/tamasheq";

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-line">
      <div className="mx-auto flex max-w-3xl flex-col gap-2 px-4 py-6 text-sm text-muted md:flex-row md:justify-between">
        <p>
          <T
            fr="Projet non commercial. Code sous licence AGPL-3.0."
            en="Non-commercial project. Code licensed under AGPL-3.0."
          />
        </p>
        <p className="flex gap-4">
          <Link href="/admin" className="hover:text-foreground">
            <T fr="Administration" en="Administration" />
          </Link>
          <a href={REPO} className="hover:text-foreground">
            <T fr="Code source" en="Source code" />
          </a>
        </p>
      </div>
    </footer>
  );
}
