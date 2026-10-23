import type { Metadata } from "next";

import { Chat } from "@/components/Chat";
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
              fr="Aucun modèle d'IA n'a encore été évalué en tamasheq. Tant que l'évaluation par des locuteurs n'est pas publiée, l'assistant reste expérimental et chaque réponse est marquée comme non vérifiée."
              en="No AI model has been evaluated in Tamasheq yet. Until the evaluation by speakers is published, the assistant stays experimental and every answer is marked as not verified."
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
              fr="TAMASHEQ n'enregistre pas les conversations et ne s'en sert pas pour entraîner un modèle. Elles sont transmises au fournisseur du modèle (Anthropic) pour produire la réponse : n'y écrivez pas d'informations personnelles ni de savoirs restreints."
              en="TAMASHEQ does not store conversations or use them to train a model. They are sent to the model provider (Anthropic) to produce the answer: do not write personal information or restricted knowledge in them."
            />
          </li>
        </ul>
      }
    >
      <Chat />
    </ModulePage>
  );
}
