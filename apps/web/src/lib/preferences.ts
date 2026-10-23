// Préférences d'affichage stockées dans le navigateur (aucune donnée envoyée au serveur).
// Elles sont appliquées sur <html> par PREFERENCES_SCRIPT avant le premier affichage,
// puis par setPreference() lors d'un changement.

export type UiLang = "fr" | "en";
export type Script = "latn" | "tfng";

export const DEFAULT_LANG: UiLang = "fr";
export const DEFAULT_SCRIPT: Script = "latn";

const KEYS = { lang: "tamasheq.lang", script: "tamasheq.script" } as const;

export const PREFERENCES_SCRIPT = `try{var d=document.documentElement,l=localStorage.getItem("${KEYS.lang}"),s=localStorage.getItem("${KEYS.script}");if(l==="fr"||l==="en"){d.dataset.lang=l;d.lang=l}if(s==="latn"||s==="tfng")d.dataset.script=s}catch(e){}`;

type Preferences = { lang: UiLang; script: Script };

const listeners = new Set<() => void>();
let snapshot: Preferences | null = null;

function read(): Preferences {
  const d = document.documentElement.dataset;
  return {
    lang: d.lang === "en" ? "en" : "fr",
    script: d.script === "tfng" ? "tfng" : "latn",
  };
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getSnapshot(): Preferences {
  snapshot ??= read();
  return snapshot;
}

const SERVER_SNAPSHOT: Preferences = { lang: DEFAULT_LANG, script: DEFAULT_SCRIPT };

export function getServerSnapshot(): Preferences {
  return SERVER_SNAPSHOT;
}

export function setPreference<K extends keyof Preferences>(key: K, value: Preferences[K]): void {
  const root = document.documentElement;
  root.dataset[key] = value;
  if (key === "lang") root.lang = value;
  try {
    localStorage.setItem(KEYS[key], value);
  } catch {
    // Stockage indisponible (navigation privée, etc.) : la préférence vaut pour cette page.
  }
  snapshot = read();
  listeners.forEach((listener) => listener());
}
