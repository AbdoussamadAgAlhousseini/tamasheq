import Link from "next/link";

import { CapabilityBadge } from "@/components/CapabilityBadge";
import { T } from "@/components/T";
import { MODULES } from "@/lib/modules";

export default function Home() {
  return (
    <>
      <h1 className="text-3xl font-semibold md:text-4xl">TAMASHEQ</h1>
      <p className="mt-4 text-lg leading-relaxed">
        <T
          fr="Une infrastructure linguistique et d'intelligence artificielle pour la langue tamasheq du Mali et les savoirs touaregs, construite avec les locuteurs et gouvernée par eux."
          en="A language and artificial intelligence infrastructure for the Tamasheq language of Mali and Tuareg knowledge, built with speakers and governed by them."
        />
      </p>
      <p role="note" className="mt-6 rounded-md border border-line bg-surface p-4 text-sm">
        <T
          fr="Le projet est en construction. Aucune fonction linguistique n'a encore été évaluée : l'état de chaque module ci-dessous est celui que déclare le serveur."
          en="The project is under construction. No language feature has been evaluated yet: the status of each module below is the one reported by the server."
        />
      </p>

      <h2 className="mt-12 text-xl font-semibold">
        <T fr="Modules" en="Modules" />
      </h2>
      <ul className="mt-4 grid gap-4 sm:grid-cols-2">
        {MODULES.map((m) => (
          <li key={m.href} className="rounded-lg border border-line bg-surface p-4">
            <h3 className="font-semibold">
              <Link href={m.href} className="hover:underline">
                <T fr={m.title.fr} en={m.title.en} />
              </Link>
            </h3>
            <p className="mt-1 text-sm text-muted">
              <T fr={m.summary.fr} en={m.summary.en} />
            </p>
            <div className="mt-3">
              <CapabilityBadge names={m.capabilities} />
            </div>
          </li>
        ))}
      </ul>

      <h2 className="mt-12 text-xl font-semibold">
        <T fr="Engagements" en="Commitments" />
      </h2>
      <ul className="prose-block mt-3">
        <li>
          <T
            fr="Aucune donnée tamasheq inventée, aucune traduction automatique présentée comme validée."
            en="No invented Tamasheq data; no machine translation presented as validated."
          />
        </li>
        <li>
          <T
            fr="Aucune performance annoncée sans méthode d'évaluation publiée."
            en="No performance claim without a published evaluation method."
          />
        </li>
        <li>
          <T
            fr="Les communautés décident de l'accès à leurs savoirs et peuvent retirer leurs contributions."
            en="Communities decide on access to their knowledge and can withdraw their contributions."
          />
        </li>
      </ul>
      <p className="mt-6">
        <Link href="/contribute" className="font-medium text-accent underline">
          <T fr="Comment contribuer" en="How to contribute" />
        </Link>
      </p>
    </>
  );
}
