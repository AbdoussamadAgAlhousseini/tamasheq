import type { Metadata } from "next";

import { Translator } from "@/components/Translator";
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
              fr="La version actuelle utilise un modèle généraliste (Claude, d'Anthropic) guidé par les entrées validées du dictionnaire. D'autres modèles, comme NLLB-200, seront comparés sur le même jeu de test, jugé par des locuteurs."
              en="The current version uses a general-purpose model (Anthropic's Claude) guided by the dictionary's validated entries. Other models, such as NLLB-200, will be compared on the same test set, judged by speakers."
            />
          </li>
        </ul>
      }
    >
      <Translator />
    </ModulePage>
  );
}
