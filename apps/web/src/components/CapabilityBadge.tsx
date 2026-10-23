"use client";

import { useEffect, useState } from "react";

import {
  type Capability,
  type CapabilityName,
  type CapabilityStatus,
  fetchCapabilities,
} from "@/lib/capabilities";

import { T } from "./T";

const LABELS: Record<CapabilityStatus, { fr: string; en: string }> = {
  not_available: { fr: "Non disponible", en: "Not available" },
  experimental: { fr: "Expérimental, non validé", en: "Experimental, not validated" },
  evaluated: { fr: "Évalué", en: "Evaluated" },
};

const NAMES: Record<CapabilityName, { fr: string; en: string }> = {
  chat: { fr: "Assistant", en: "Assistant" },
  translation: { fr: "Traduction", en: "Translation" },
  dictionary: { fr: "Dictionnaire", en: "Dictionary" },
  knowledge: { fr: "Savoirs", en: "Knowledge" },
  asr: { fr: "Reconnaissance vocale", en: "Speech recognition" },
  tts: { fr: "Synthèse vocale", en: "Speech synthesis" },
};

type State = { kind: "loading" } | { kind: "error" } | { kind: "ok"; items: Capability[] };

/** Affiche l'état déclaré par l'API ; ne présume jamais qu'une fonction est disponible. */
export function CapabilityBadge({ names }: { names: CapabilityName[] }) {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    fetchCapabilities()
      .then((all) => active && setState({ kind: "ok", items: all }))
      .catch(() => active && setState({ kind: "error" }));
    return () => {
      active = false;
    };
  }, []);

  return (
    <ul className="flex flex-wrap gap-2" aria-live="polite">
      {names.map((name) => {
        const status =
          state.kind === "ok" ? state.items.find((c) => c.name === name)?.status : undefined;
        return (
          <li
            key={name}
            data-capability={name}
            data-status={status ?? state.kind}
            className="rounded-full border border-line px-3 py-1 text-xs"
          >
            {names.length > 1 && (
              <>
                <T fr={NAMES[name].fr} en={NAMES[name].en} /> :{" "}
              </>
            )}
            {state.kind === "loading" && <T fr="État en cours de vérification…" en="Checking status…" />}
            {state.kind === "error" && (
              <T fr="État inconnu (serveur injoignable)" en="Unknown status (server unreachable)" />
            )}
            {state.kind === "ok" &&
              (status ? (
                <T fr={LABELS[status].fr} en={LABELS[status].en} />
              ) : (
                <T fr="Non déclaré par le serveur" en="Not declared by the server" />
              ))}
          </li>
        );
      })}
    </ul>
  );
}
