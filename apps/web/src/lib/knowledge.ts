// Contrats de /api/v1/knowledge (services/api/app/routers/knowledge.py).
import { postJson } from "./api";
import { API_URL } from "./capabilities";

export type Theme =
  | "oral_history"
  | "proverbs"
  | "culture"
  | "pastoralism"
  | "environment"
  | "plants"
  | "toponymy"
  | "crafts"
  | "intergenerational"
  | "language";

export const THEMES: Record<Theme, { fr: string; en: string }> = {
  oral_history: { fr: "Histoire orale", en: "Oral history" },
  proverbs: { fr: "Proverbes et expressions", en: "Proverbs and expressions" },
  culture: { fr: "Culture et transmission", en: "Culture and transmission" },
  pastoralism: { fr: "Pastoralisme et mobilité", en: "Pastoralism and mobility" },
  environment: { fr: "Environnement et ressources", en: "Environment and resources" },
  plants: { fr: "Plantes et savoirs écologiques", en: "Plants and ecological knowledge" },
  toponymy: { fr: "Noms de lieux", en: "Place names" },
  crafts: { fr: "Artisanat et pratiques", en: "Crafts and practices" },
  intergenerational: {
    fr: "Savoirs des femmes, des jeunes et des anciens",
    en: "Knowledge of women, youth and elders",
  },
  language: { fr: "Documentation linguistique", en: "Language documentation" },
};

type Source = { title: string; citation: string | null; url: string | null };

export type DocumentSummary = {
  id: string;
  title: string;
  theme: Theme;
  access_level: "public" | "community";
  language: string;
  author_credit: string | null;
  source: Source;
  license: string;
  excerpt: string;
};

export type AskResult = {
  answer: string | null;
  insufficient_documentation: boolean;
  references: {
    ref: string;
    document_id: string;
    title: string;
    source: Source;
    license: string;
    passage: string;
  }[];
  provider: string | null;
  model: string | null;
  status: "experimental";
  verified: false;
};

export async function searchKnowledge(
  q: string,
  theme: Theme | "",
  signal?: AbortSignal,
): Promise<DocumentSummary[]> {
  const params = new URLSearchParams({ q });
  if (theme) params.set("theme", theme);
  const response = await fetch(`${API_URL}/api/v1/knowledge?${params}`, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as DocumentSummary[];
}

export async function fetchDocument(id: string): Promise<{ body: string }> {
  const response = await fetch(`${API_URL}/api/v1/knowledge/${id}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()) as { body: string };
}

export function ask(question: string): Promise<AskResult> {
  return postJson<AskResult>("/api/v1/knowledge/ask", { question });
}
