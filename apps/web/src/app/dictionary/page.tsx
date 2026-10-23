import type { Metadata } from "next";

import { DictionarySearch } from "@/components/DictionarySearch";
import { ModulePage } from "@/components/ModulePage";
import { T } from "@/components/T";
import { getModule } from "@/lib/modules";

export const metadata: Metadata = { title: "Dictionnaire" };

export default function Page() {
  return (
    <ModulePage
      module={getModule("/dictionary")}
      planned={
        <ul>
          <li>
            <T
              fr="Pour chaque entrée : graphies latines, graphies tifinagh validées, définitions, traductions, variantes, exemples, catégorie grammaticale si connue, prononciation."
              en="For each entry: Latin spellings, validated Tifinagh spellings, definitions, translations, variants, examples, part of speech if known, pronunciation."
            />
          </li>
          <li>
            <T
              fr="Recherche selon des règles de normalisation documentées, dans les deux écritures."
              en="Search following documented normalisation rules, in both scripts."
            />
          </li>
          <li>
            <T
              fr="Sources, droits d'utilisation et statut de validation affichés pour chaque entrée."
              en="Sources, usage rights and validation status shown for each entry."
            />
          </li>
        </ul>
      }
      limits={
        <ul>
          <li>
            <T
              fr="Aucune définition n'est générée pour remplir le dictionnaire."
              en="No definition is generated to fill the dictionary."
            />
          </li>
          <li>
            <T
              fr="Une entrée provisoire est toujours distinguée d'une entrée validée."
              en="A provisional entry is always distinguished from a validated one."
            />
          </li>
          <li>
            <T
              fr="La conversion entre écriture latine et tifinagh n'est pas automatique caractère par caractère : les formes tifinagh sont validées par des locuteurs."
              en="Conversion between Latin and Tifinagh script is not automatic character by character: Tifinagh forms are validated by speakers."
            />
          </li>
        </ul>
      }
    >
      <DictionarySearch />
    </ModulePage>
  );
}
