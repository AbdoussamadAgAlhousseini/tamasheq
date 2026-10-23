// Contrat de POST /api/v1/translate (services/api/app/routers/translate.py).
import { postJson } from "./api";

export type Lang = "taq" | "fr" | "en";

export type TranslationResult = {
  translation: string;
  alternatives: string[];
  ambiguities: string[];
  notes: string;
  glossary: { id: string; headword: string }[];
  provider: string;
  model: string;
  truncated: boolean;
  status: "experimental";
  verified: false;
};

export const DIRECTIONS: { source: Lang; target: Lang; fr: string; en: string }[] = [
  { source: "fr", target: "taq", fr: "Français → tamasheq", en: "French → Tamasheq" },
  { source: "taq", target: "fr", fr: "Tamasheq → français", en: "Tamasheq → French" },
  { source: "en", target: "taq", fr: "Anglais → tamasheq", en: "English → Tamasheq" },
  { source: "taq", target: "en", fr: "Tamasheq → anglais", en: "Tamasheq → English" },
];

export function translate(
  text: string,
  source: Lang,
  target: Lang,
  variant: string,
): Promise<TranslationResult> {
  return postJson<TranslationResult>("/api/v1/translate", {
    text,
    source_lang: source,
    target_lang: target,
    variant: variant.trim() || null,
  });
}

export function langTag(lang: Lang): string {
  return lang === "taq" ? "taq-Latn" : lang;
}
