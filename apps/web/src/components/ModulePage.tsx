import type { ReactNode } from "react";

import type { Module } from "@/lib/modules";

import { CapabilityBadge } from "./CapabilityBadge";
import { T } from "./T";

/** Gabarit des pages de modules : ce qui est prévu, ce qui ne l'est pas encore, et l'état réel. */
export function ModulePage({
  module,
  planned,
  limits,
}: {
  module: Module;
  planned: ReactNode;
  limits: ReactNode;
}) {
  return (
    <>
      <h1 className="text-3xl font-semibold">
        <T fr={module.title.fr} en={module.title.en} />
      </h1>
      <p className="mt-3 text-lg text-muted">
        <T fr={module.summary.fr} en={module.summary.en} />
      </p>
      <div className="mt-6">
        <CapabilityBadge names={module.capabilities} />
      </div>
      <section className="mt-10" aria-labelledby="planned">
        <h2 id="planned" className="text-xl font-semibold">
          <T fr="Ce qui est prévu" en="What is planned" />
        </h2>
        <div className="prose-block mt-3">{planned}</div>
      </section>
      <section className="mt-10" aria-labelledby="limits">
        <h2 id="limits" className="text-xl font-semibold">
          <T fr="Limites et garanties" en="Limits and safeguards" />
        </h2>
        <div className="prose-block mt-3">{limits}</div>
      </section>
    </>
  );
}
