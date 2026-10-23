import type { Metadata } from "next";

import { ModulePage } from "@/components/ModulePage";
import { T } from "@/components/T";
import { getModule } from "@/lib/modules";

export const metadata: Metadata = { title: "Voix" };

export default function Page() {
  return (
    <ModulePage
      module={getModule("/voice")}
      planned={
        <ul>
          <li>
            <T
              fr="Reconnaissance automatique de la parole (audio vers texte) et synthèse vocale (texte vers audio), développées séparément."
              en="Automatic speech recognition (audio to text) and speech synthesis (text to audio), developed separately."
            />
          </li>
          <li>
            <T
              fr="Enregistrement depuis le navigateur, écoute, et correction manuelle des transcriptions."
              en="Recording from the browser, playback, and manual correction of transcriptions."
            />
          </li>
        </ul>
      }
      limits={
        <ul>
          <li>
            <T
              fr="Whisper ne prend pas en charge le tamasheq. Les autres modèles candidats doivent être mesurés sur des enregistrements représentatifs."
              en="Whisper does not support Tamasheq. Other candidate models must be measured on representative recordings."
            />
          </li>
          <li>
            <T
              fr="Aucune voix générique ne sera présentée comme une voix tamasheq naturelle."
              en="No generic voice will be presented as a natural Tamasheq voice."
            />
          </li>
          <li>
            <T
              fr="Chaque enregistrement exige un consentement documenté et peut être retiré."
              en="Every recording requires documented consent and can be withdrawn."
            />
          </li>
        </ul>
      }
    />
  );
}
