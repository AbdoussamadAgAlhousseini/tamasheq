"use client";

import { useEffect, useState } from "react";

import { type Entry, formsByScript, searchDictionary } from "@/lib/dictionary";

import { T } from "./T";
import { TaqText } from "./TaqText";

type State = { kind: "loading" } | { kind: "error" } | { kind: "ok"; entries: Entry[] };

function Localized({ fr, en }: { fr: string | null; en: string | null }) {
  // Les deux langues : selon la langue d'interface. Une seule : affichée dans tous les cas.
  if (fr && en) return <T fr={fr} en={en} />;
  if (fr) return <span lang="fr">{fr}</span>;
  if (en) return <span lang="en">{en}</span>;
  return null;
}

function EntryCard({ entry }: { entry: Entry }) {
  const scripts = new Set([entry.script, ...entry.spellings.map((s) => s.script)]);
  return (
    <article className="rounded-lg border border-line bg-surface p-4" data-entry={entry.id}>
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="text-xl font-semibold">
          <TaqText forms={formsByScript(entry)} />
        </h3>
        {entry.part_of_speech && <span className="text-sm text-muted">{entry.part_of_speech}</span>}
        <span
          data-status={entry.status}
          className={`rounded-full border px-2 py-0.5 text-xs ${
            entry.status === "validated" ? "border-line" : "border-current font-medium"
          }`}
        >
          {entry.status === "validated" ? (
            <T fr="Validée" en="Validated" />
          ) : (
            <T fr="Non validée : en attente de relecture" en="Not validated: awaiting review" />
          )}
        </span>
      </header>

      {scripts.size > 1 || entry.spellings.length > 1 ? (
        <p className="mt-1 text-sm text-muted">
          <T fr="Graphies : " en="Spellings: " />
          {[{ form: entry.headword, script: entry.script }, ...entry.spellings]
            .map((s) => s.form)
            .filter((form, i, all) => all.indexOf(form) === i)
            .map((form, i) => (
              <span key={form}>
                {i > 0 && " · "}
                <span lang="taq">{form}</span>
              </span>
            ))}
        </p>
      ) : null}
      {entry.variant && (
        <p className="mt-1 text-sm text-muted">
          <T fr="Variante : " en="Variety: " />
          {entry.variant}
        </p>
      )}

      <ol className="mt-3 list-decimal space-y-2 pl-5">
        {entry.senses.map((sense, i) => (
          <li key={i}>
            {(sense.translation_fr || sense.translation_en) && (
              <p className="font-medium">
                <Localized fr={sense.translation_fr} en={sense.translation_en} />
              </p>
            )}
            {(sense.definition_fr || sense.definition_en) && (
              <p>
                <Localized fr={sense.definition_fr} en={sense.definition_en} />
              </p>
            )}
            {sense.examples.map((ex, j) => (
              <p key={j} className="mt-1 border-l-2 border-line pl-3 text-sm">
                <span lang={`taq-${ex.script}`}>{ex.text}</span>
                {(ex.translation_fr || ex.translation_en) && (
                  <span className="text-muted">
                    {" — "}
                    <Localized fr={ex.translation_fr} en={ex.translation_en} />
                  </span>
                )}
              </p>
            ))}
          </li>
        ))}
      </ol>

      <p className="mt-3 text-xs text-muted">
        <T fr="Source : " en="Source: " />
        {entry.source.url ? <a href={entry.source.url} className="underline">{entry.source.title}</a> : entry.source.title}
        {" · "}
        <T fr="Droits : " en="Rights: " />
        {entry.license}
      </p>
    </article>
  );
}

export function DictionarySearch() {
  const [query, setQuery] = useState("");
  const [includePending, setIncludePending] = useState(false);
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setState({ kind: "loading" });
      searchDictionary(query.trim(), includePending, controller.signal)
        .then((entries) => setState({ kind: "ok", entries }))
        .catch((e: unknown) => {
          if (!(e instanceof DOMException && e.name === "AbortError")) setState({ kind: "error" });
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, includePending]);

  return (
    <section aria-labelledby="dict-search">
      <h2 id="dict-search" className="sr-only">
        <T fr="Recherche" en="Search" />
      </h2>
      <label htmlFor="dict-q" className="text-sm font-medium">
        <T
          fr="Rechercher un mot (latin, tifinagh, français ou anglais)"
          en="Search a word (Latin, Tifinagh, French or English)"
        />
      </label>
      <input
        id="dict-q"
        type="search"
        dir="auto"
        maxLength={200}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="mt-1 block w-full rounded-md border border-line bg-background p-2"
      />
      <label className="mt-3 flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={includePending}
          onChange={(e) => setIncludePending(e.target.checked)}
        />
        <T
          fr="Afficher aussi les entrées en attente de validation"
          en="Also show entries awaiting validation"
        />
      </label>

      <div className="mt-6" aria-live="polite">
        {state.kind === "loading" && (
          <p className="text-sm text-muted">
            <T fr="Recherche…" en="Searching…" />
          </p>
        )}
        {state.kind === "error" && (
          <p role="alert" className="text-sm font-medium">
            <T fr="Serveur injoignable." en="Server unreachable." />
          </p>
        )}
        {state.kind === "ok" && state.entries.length === 0 && (
          <p className="text-sm">
            {query.trim() ? (
              <T fr="Aucun résultat." en="No results." />
            ) : (
              <T
                fr="Aucune entrée publiée pour l'instant : le dictionnaire se remplit à mesure que des locuteurs valident les contributions."
                en="No published entries yet: the dictionary fills up as speakers validate contributions."
              />
            )}
          </p>
        )}
        {state.kind === "ok" && state.entries.length > 0 && (
          <ul className="flex flex-col gap-4">
            {state.entries.map((entry) => (
              <li key={entry.id}>
                <EntryCard entry={entry} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
