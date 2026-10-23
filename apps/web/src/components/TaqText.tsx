import type { Script } from "@/lib/dictionary";

/**
 * Texte tamasheq disponible dans une ou deux écritures. Quand les deux existent, la feuille de
 * style n'affiche que celle choisie dans l'en-tête (attribut data-script de <html>). Aucune
 * forme n'est jamais déduite de l'autre : on n'affiche que ce qui a été saisi et validé.
 */
export function TaqText({ forms }: { forms: Partial<Record<Script, string>> }) {
  const { Latn: latn, Tfng: tfng } = forms;
  if (latn && tfng) {
    return (
      <>
        <span lang="taq-Latn" data-taq-alt="latn">
          {latn}
        </span>
        <span lang="taq-Tfng" data-taq-alt="tfng">
          {tfng}
        </span>
      </>
    );
  }
  const only = latn ?? tfng ?? "";
  return <span lang={latn ? "taq-Latn" : "taq-Tfng"}>{only}</span>;
}
