import type { Metadata } from "next";

import { T } from "@/components/T";

export const metadata: Metadata = { title: "À propos" };

const DOCS = "https://github.com/AbdoussamadAgAlhousseini/tamasheq/blob/main/docs";

// Caractères attribués du bloc Unicode Tifinagh (U+2D30–U+2D7F) : U+2D30–U+2D67, U+2D6F,
// U+2D70, U+2D7F. C'est le répertoire Unicode complet, toutes langues confondues, et non une
// convention orthographique tamasheq.
const TIFINAGH_BLOCK = [
  ...Array.from({ length: 0x2d67 - 0x2d30 + 1 }, (_, i) => 0x2d30 + i),
  0x2d6f,
  0x2d70,
  0x2d7f,
];

const hex = (cp: number) => `U+${cp.toString(16).toUpperCase()}`;

export default function Page() {
  return (
    <>
      <h1 className="text-3xl font-semibold">
        <T fr="À propos" en="About" />
      </h1>

      <section className="mt-8" aria-labelledby="vision">
        <h2 id="vision" className="text-xl font-semibold">
          <T fr="Vision" en="Vision" />
        </h2>
        <div className="prose-block mt-3">
          <p>
            <T
              fr="TAMASHEQ veut doter la langue tamasheq d'outils numériques fiables : assistant, traducteur, dictionnaire, technologies vocales et bibliothèque de savoirs. Le projet commence par le tamasheq du Mali (code ISO 639-3 : taq)."
              en="TAMASHEQ aims to give the Tamasheq language reliable digital tools: assistant, translator, dictionary, speech technology and a knowledge library. The project starts with the Tamasheq of Mali (ISO 639-3 code: taq)."
            />
          </p>
          <p>
            <T
              fr="Le projet est non commercial. Il part de modèles existants, les évalue publiquement, et ne les adapte que lorsque des données autorisées et des résultats mesurés le justifient."
              en="The project is non-commercial. It starts from existing models, evaluates them publicly, and only adapts them when authorised data and measured results justify it."
            />
          </p>
        </div>
      </section>

      <section className="mt-10" aria-labelledby="governance">
        <h2 id="governance" className="text-xl font-semibold">
          <T fr="Gouvernance des données" en="Data governance" />
        </h2>
        <div className="prose-block mt-3">
          <p>
            <T
              fr="Le projet suit les principes CARE pour la gouvernance des données autochtones : bénéfice collectif, autorité de contrôle, responsabilité et éthique (Carroll et al., Data Science Journal, 2020)."
              en="The project follows the CARE Principles for Indigenous Data Governance: collective benefit, authority to control, responsibility and ethics (Carroll et al., Data Science Journal, 2020)."
            />
          </p>
          <p>
            <T
              fr="Les locuteurs et les communautés sont des partenaires de la gouvernance, pas de simples fournisseurs de contenu."
              en="Speakers and communities are partners in governance, not mere content providers."
            />
          </p>
        </div>
      </section>

      <section className="mt-10" aria-labelledby="scripts">
        <h2 id="scripts" className="text-xl font-semibold">
          <T fr="Écritures" en="Scripts" />
        </h2>
        <div className="prose-block mt-3">
          <p>
            <T
              fr="Le tamasheq s'écrit en alphabet latin et en tifinagh. Le sélecteur « Écriture tamasheq » de l'en-tête enregistre votre préférence ; il choisit la forme affichée quand un mot existe dans les deux écritures, par exemple dans le dictionnaire."
              en="Tamasheq is written in Latin script and in Tifinagh. The “Tamasheq script” selector in the header saves your preference; it chooses which form is shown when a word exists in both scripts, for example in the dictionary."
            />
          </p>
          <p>
            <T
              fr="Contrôle d'affichage : voici l'ensemble des caractères du bloc Unicode Tifinagh. Il couvre plusieurs langues et ne constitue pas une convention orthographique tamasheq. Si des carrés vides apparaissent, la police n'a pas pu être chargée."
              en="Display check: below is every character of the Unicode Tifinagh block. It covers several languages and is not a Tamasheq spelling convention. If empty boxes appear, the font could not be loaded."
            />
          </p>
        </div>
        <ul
          className="mt-4 grid grid-cols-[repeat(auto-fill,minmax(4.5rem,1fr))] gap-2"
          data-testid="tifinagh-block"
        >
          {TIFINAGH_BLOCK.map((cp) => (
            <li key={cp} className="rounded border border-line bg-surface p-2 text-center">
              <span lang="und-Tfng" className="block text-2xl">
                {String.fromCodePoint(cp)}
              </span>
              <span className="block font-mono text-[0.65rem] text-muted">{hex(cp)}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-10" aria-labelledby="sources">
        <h2 id="sources" className="text-xl font-semibold">
          <T fr="Sources et documentation" en="Sources and documentation" />
        </h2>
        <ul className="prose-block mt-3">
          <li>
            <a href={`${DOCS}/research-and-sources.md`}>
              <T fr="Recherche et sources" en="Research and sources" />
            </a>
          </li>
          <li>
            <a href={`${DOCS}/phase-0-report.md`}>
              <T fr="Rapport de cadrage" en="Scoping report" />
            </a>
          </li>
          <li>
            <a href={`${DOCS}/decisions.md`}>
              <T fr="Registre des décisions" en="Decision log" />
            </a>
          </li>
        </ul>
        <p className="mt-4 text-sm text-muted">
          <T
            fr="Police tifinagh : Noto Sans Tifinagh, licence SIL Open Font License 1.1."
            en="Tifinagh font: Noto Sans Tifinagh, SIL Open Font License 1.1."
          />
        </p>
      </section>
    </>
  );
}
