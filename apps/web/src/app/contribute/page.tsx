import type { Metadata } from "next";

import { T } from "@/components/T";

export const metadata: Metadata = { title: "Contribuer" };

export default function Page() {
  return (
    <>
      <h1 className="text-3xl font-semibold">
        <T fr="Contribuer" en="Contribute" />
      </h1>
      <p role="note" className="mt-6 rounded-md border border-line bg-surface p-4 text-sm">
        <T
          fr="Les contributions ne sont pas encore ouvertes. Elles le seront quand les règles de consentement et de validation seront en place."
          en="Contributions are not open yet. They will open once consent and validation rules are in place."
        />
      </p>

      <section className="mt-10" aria-labelledby="what">
        <h2 id="what" className="text-xl font-semibold">
          <T fr="Contributions prévues" en="Planned contributions" />
        </h2>
        <ul className="prose-block mt-3">
          <li>
            <T fr="Mots, expressions et exemples d'usage." en="Words, expressions and usage examples." />
          </li>
          <li>
            <T fr="Corrections de traductions." en="Translation corrections." />
          </li>
          <li>
            <T fr="Enregistrements de phrases lues." en="Recordings of read sentences." />
          </li>
          <li>
            <T fr="Documents et récits, avec leurs conditions d'accès." en="Documents and stories, with their access conditions." />
          </li>
        </ul>
      </section>

      <section className="mt-10" aria-labelledby="consent">
        <h2 id="consent" className="text-xl font-semibold">
          <T fr="Vos droits" en="Your rights" />
        </h2>
        <ul className="prose-block mt-3">
          <li>
            <T
              fr="Vous pourrez contribuer sous pseudonyme ; votre adresse e-mail ne sera jamais publiée."
              en="You will be able to contribute under a pseudonym; your email address will never be published."
            />
          </li>
          <li>
            <T
              fr="Autoriser la publication d'une contribution et autoriser son usage pour entraîner un modèle sont deux choix distincts."
              en="Allowing a contribution to be published and allowing it to train a model are two separate choices."
            />
          </li>
          <li>
            <T
              fr="Vous pourrez retirer une contribution ; le projet indiquera dans quels jeux de données elle avait été intégrée."
              en="You will be able to withdraw a contribution; the project will state which datasets it had been included in."
            />
          </li>
        </ul>
      </section>
    </>
  );
}
