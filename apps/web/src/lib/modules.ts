import type { CapabilityName } from "./capabilities";

export type Text = { fr: string; en: string };

export type Module = {
  href: string;
  title: Text;
  summary: Text;
  capabilities: CapabilityName[];
};

// Modules fonctionnels du cadrage (docs/phase-0-report.md). Les descriptions disent ce qui est
// prévu, jamais ce qui fonctionne : l'état réel vient de l'API.
export const MODULES: Module[] = [
  {
    href: "/chat",
    title: { fr: "Assistant", en: "Assistant" },
    summary: {
      fr: "Répondre en tamasheq, en français et en anglais, en signalant ses incertitudes.",
      en: "Answer in Tamasheq, French and English, stating its uncertainty.",
    },
    capabilities: ["chat"],
  },
  {
    href: "/translate",
    title: { fr: "Traduction", en: "Translation" },
    summary: {
      fr: "Tamasheq ⇄ français et tamasheq ⇄ anglais, avec ambiguïtés et variantes affichées.",
      en: "Tamasheq ⇄ French and Tamasheq ⇄ English, showing ambiguities and variants.",
    },
    capabilities: ["translation"],
  },
  {
    href: "/dictionary",
    title: { fr: "Dictionnaire", en: "Dictionary" },
    summary: {
      fr: "Entrées en écriture latine et tifinagh, avec sources et statut de validation.",
      en: "Entries in Latin and Tifinagh script, with sources and validation status.",
    },
    capabilities: ["dictionary"],
  },
  {
    href: "/knowledge",
    title: { fr: "Savoirs", en: "Knowledge" },
    summary: {
      fr: "Bibliothèque de savoirs touaregs, avec provenance, droits et niveaux d'accès.",
      en: "Library of Tuareg knowledge, with provenance, rights and access levels.",
    },
    capabilities: ["knowledge"],
  },
  {
    href: "/voice",
    title: { fr: "Voix", en: "Voice" },
    summary: {
      fr: "Reconnaissance de la parole et synthèse vocale, évaluées par des locuteurs.",
      en: "Speech recognition and speech synthesis, evaluated by speakers.",
    },
    capabilities: ["asr", "tts"],
  },
];

export const NAV: { href: string; label: Text }[] = [
  ...MODULES.map((m) => ({ href: m.href, label: m.title })),
  { href: "/contribute", label: { fr: "Contribuer", en: "Contribute" } },
  { href: "/about", label: { fr: "À propos", en: "About" } },
];

export function getModule(href: string): Module {
  const found = MODULES.find((m) => m.href === href);
  if (!found) throw new Error(`Module inconnu : ${href}`);
  return found;
}
