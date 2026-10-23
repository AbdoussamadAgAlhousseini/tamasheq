import type { Metadata } from "next";

import { ModulePage } from "@/components/ModulePage";
import { T } from "@/components/T";
import { getModule } from "@/lib/modules";

export const metadata: Metadata = { title: "Traduction" };

export default function Page() {
  return (
    <ModulePage
      module={getModule("/translate")}
      planned={
        <ul>
          <li>
            <T
              fr="Directions : tamasheq → français, français → tamasheq, tamasheq → anglais, anglais → tamasheq."
              en="Directions: Tamasheq → French, French → Tamasheq, Tamasheq → English, English → Tamasheq."
            />
          </li>
          <li>
            <T
              fr="Pour chaque traduction : texte original, proposition, variante linguistique, ambiguïtés et statut (expérimental ou validé)."
              en="For each translation: source text, proposal, language variety, ambiguities and status (experimental or validated)."
            />
          </li>
          <li>
            <T
              fr="Correction des traductions et propositions de variantes par des locuteurs habilités."
              en="Corrections and alternative proposals by authorised speakers."
            />
          </li>
        </ul>
      }
      limits={
        <ul>
          <li>
            <T
              fr="Une traduction automatique n'est jamais une traduction certifiée."
              en="A machine translation is never a certified translation."
            />
          </li>
          <li>
            <T
              fr="Les modèles candidats (par exemple NLLB-200) doivent d'abord être évalués sur un jeu de test indépendant, jugé par des locuteurs."
              en="Candidate models (for example NLLB-200) must first be evaluated on an independent test set, judged by speakers."
            />
          </li>
        </ul>
      }
    />
  );
}
