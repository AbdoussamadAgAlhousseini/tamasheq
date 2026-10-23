import type { ReactNode } from "react";

/**
 * Texte d'interface bilingue. Les deux langues sont dans le HTML ; la feuille de style masque
 * celle qui n'est pas choisie (attribut data-lang de <html>), sans clignotement ni requête.
 * Ne sert qu'aux textes d'interface : jamais aux contenus tamasheq.
 */
export function T({ fr, en }: { fr: ReactNode; en: ReactNode }) {
  return (
    <>
      <span lang="fr" data-ui-lang="fr">
        {fr}
      </span>
      <span lang="en" data-ui-lang="en">
        {en}
      </span>
    </>
  );
}
