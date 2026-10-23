import type { Metadata } from "next";

import { KnowledgeSearch } from "@/components/KnowledgeSearch";
import { ModulePage } from "@/components/ModulePage";
import { T } from "@/components/T";
import { getModule } from "@/lib/modules";

export const metadata: Metadata = { title: "Savoirs" };

export default function Page() {
  return (
    <ModulePage
      module={getModule("/knowledge")}
      planned={
        <>
          <p>
            <T
              fr="Une bibliothèque documentaire sur l'histoire orale, les proverbes, le pastoralisme et la mobilité, l'environnement, les plantes, la toponymie, l'artisanat, les savoirs des femmes, des jeunes et des anciens, et la documentation linguistique."
              en="A document library on oral history, proverbs, pastoralism and mobility, environment, plants, place names, crafts, the knowledge of women, young people and elders, and language documentation."
            />
          </p>
          <p>
            <T
              fr="Chaque document aura une provenance, un contributeur s'il accepte d'être nommé, une date, un régime de droits et un statut de validation."
              en="Each document will have a provenance, a contributor if they agree to be named, a date, a rights regime and a validation status."
            />
          </p>
        </>
      }
      limits={
        <ul>
          <li>
            <T
              fr="Les savoirs sensibles, sacrés, familiaux ou territoriaux ne sont ni publiés ni utilisés pour entraîner un modèle sans autorisation."
              en="Sensitive, sacred, family or territorial knowledge is neither published nor used to train a model without permission."
            />
          </li>
          <li>
            <T
              fr="Trois niveaux d'accès : public, réservé aux membres, restreint. Un document restreint n'est jamais servi par le site ; les réponses générées ne s'appuient que sur des documents publics, les seuls transmis au fournisseur du modèle."
              en="Three access levels: public, members only, restricted. A restricted document is never served by the site; generated answers rely only on public documents, the only ones sent to the model provider."
            />
          </li>
        </ul>
      }
    >
      <KnowledgeSearch />
    </ModulePage>
  );
}
