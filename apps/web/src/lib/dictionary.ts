// Contrat de GET /api/v1/dictionary (services/api/app/routers/dictionary.py).
import { API_URL } from "./capabilities";

export type Script = "Latn" | "Tfng";

export type Entry = {
  id: string;
  headword: string;
  script: Script;
  language: string;
  variant: string | null;
  part_of_speech: string | null;
  status: "validated" | "pending";
  spellings: { form: string; script: Script }[];
  senses: {
    definition_fr: string | null;
    definition_en: string | null;
    translation_fr: string | null;
    translation_en: string | null;
    examples: {
      text: string;
      script: Script;
      translation_fr: string | null;
      translation_en: string | null;
    }[];
  }[];
  source: { title: string; citation: string | null; url: string | null };
  license: string;
  validated_at: string | null;
};

export async function searchDictionary(
  q: string,
  includePending: boolean,
  signal?: AbortSignal,
): Promise<Entry[]> {
  const params = new URLSearchParams({ q, include_pending: String(includePending) });
  const response = await fetch(`${API_URL}/api/v1/dictionary?${params}`, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return ((await response.json()) as { items: Entry[] }).items;
}

/** Première forme disponible dans chaque écriture : l'entrée elle-même, puis ses graphies. */
export function formsByScript(entry: Entry): Partial<Record<Script, string>> {
  const forms: Partial<Record<Script, string>> = { [entry.script]: entry.headword };
  for (const s of entry.spellings) forms[s.script] ??= s.form;
  return forms;
}
