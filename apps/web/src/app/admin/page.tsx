import type { Metadata } from "next";

import { T } from "@/components/T";

export const metadata: Metadata = {
  title: "Administration",
  robots: { index: false, follow: false },
};

export default function Page() {
  return (
    <>
      <h1 className="text-3xl font-semibold">
        <T fr="Administration" en="Administration" />
      </h1>
      <p className="mt-4">
        <T
          fr="Cet espace servira à valider les contributions, gérer les rôles et traiter les demandes de retrait."
          en="This area will be used to validate contributions, manage roles and handle withdrawal requests."
        />
      </p>
      <p role="note" className="mt-6 rounded-md border border-line bg-surface p-4 text-sm">
        <T
          fr="Accès réservé. L'authentification n'est pas encore en place : aucune action d'administration n'est possible."
          en="Restricted access. Authentication is not in place yet: no administration action is possible."
        />
      </p>
    </>
  );
}
