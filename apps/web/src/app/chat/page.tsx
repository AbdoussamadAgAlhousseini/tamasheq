import type { Metadata } from "next";

import { ModulePage } from "@/components/ModulePage";
import { T } from "@/components/T";
import { getModule } from "@/lib/modules";

export const metadata: Metadata = { title: "Assistant" };

export default function Page() {
  return (
    <ModulePage
      module={getModule("/chat")}
      planned={
        <ul>
          <li>
            <T
              fr="Comprendre des questions en tamasheq et répondre en tamasheq, en français ou en anglais."
              en="Understand questions in Tamasheq and answer in Tamasheq, French or English."
            />
          </li>
          <li>
            <T
              fr="Expliquer des mots, des expressions et des proverbes documentés, avec leurs sources."
              en="Explain documented words, expressions and proverbs, with their sources."
            />
          </li>
          <li>
            <T
              fr="Garder le contexte d'une conversation pendant la session uniquement."
              en="Keep the context of a conversation during the session only."
            />
          </li>
        </ul>
      }
      limits={
        <ul>
          <li>
            <T
              fr="Aucun modèle d'IA n'a encore été évalué en tamasheq. L'assistant ne sera ouvert qu'avec une mention claire de ses capacités mesurées."
              en="No AI model has been evaluated in Tamasheq yet. The assistant will only open with a clear statement of its measured abilities."
            />
          </li>
          <li>
            <T
              fr="Il devra distinguer une connaissance documentée d'une réponse générée par un modèle, et signaler ses incertitudes."
              en="It will have to distinguish documented knowledge from model-generated answers, and state its uncertainty."
            />
          </li>
          <li>
            <T
              fr="Les conversations ne servent pas à entraîner un modèle."
              en="Conversations are not used to train a model."
            />
          </li>
        </ul>
      }
    />
  );
}
