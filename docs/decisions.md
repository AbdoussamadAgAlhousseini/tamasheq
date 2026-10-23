# Registre des décisions

Chaque décision structurante est datée et attribuée. Une décision peut être révisée ; on
ajoute alors une nouvelle entrée plutôt que d'effacer l'ancienne.

| # | Date | Décision | Décidé par | Conséquences |
|---|---|---|---|---|
| D1 | 2026-10-23 | Le projet s'appelle **TAMASHEQ** (dépôt `tamasheq`). Le nom « AKAL Tamasheq » du cadrage initial est abandonné. | Porteur du projet | Renommage du dépôt et des documents. |
| D2 | 2026-10-23 | Projet **non commercial**. | Porteur du projet | Les modèles et données sous licence NC (NLLB-200, MMS) sont utilisables pour la recherche et le service non commercial. La clause **ND** du corpus IWSLT2022 reste un frein à l'adaptation et à la redistribution : usage en évaluation uniquement sans accord écrit. |
| D3 | 2026-10-23 | Priorité au **tamasheq du Mali, code ISO 639-3 `taq`**. | Porteur du projet | Toute donnée porte le code `taq` et un champ de variante (région, communauté) ; les autres variétés (`ttq`, `thv`, `thz`) restent prévues dans le schéma mais hors priorité. |
| D4 | 2026-10-23 | Conventions orthographiques de référence et habilitation des réviseurs : **décidées par le porteur du projet**. | Porteur du projet | Les conventions seront saisies comme données versionnées, pas codées en dur. À documenter dans `docs/orthography.md` (phase 4). |
| D5 | 2026-10-23 | Gouvernance des accès restreints et des retraits : **décidée par le porteur du projet**. | Porteur du projet | Le rôle `admin` porte cette décision dans l'application ; la procédure sera écrite dans `docs/data-governance.md`. |
| D6 | 2026-10-23 | L'envoi de **textes publics** à une API d'IA externe est accepté. | Porteur du projet | Les contenus restreints ne sont jamais envoyés à une API externe. Fournisseur initial proposé pour la phase 3 : Claude (Anthropic), derrière un adaptateur remplaçable ; à comparer à d'autres fournisseurs sur le jeu de test. |
| D7 | 2026-10-23 | Hébergement : **choix délégué**, voir la recommandation dans `docs/deployment.md`. | Délégué | Recommandation : services managés en région Europe ; à confirmer avant la phase 8. |
| D8 | 2026-10-23 | Prise de contact avec le LIA, Fondation Hirondelle ou Masakhane : **pas nécessaire pour l'instant**. | Porteur du projet | Le corpus IWSLT2022 reste limité à l'évaluation non commerciale avec citation. |
| D9 | 2026-10-23 | Le code sera **open source**. | Porteur du projet | Licence du code choisie en D10. Une licence open source autorise par définition l'usage commercial **du code** ; le caractère non commercial s'applique aux données et aux modèles, qui ont leurs propres licences. |
| D10 | 2026-10-23 | Licence du code : **GNU AGPL-3.0**. | Porteur du projet | Fichier `LICENSE` ajouté. Ne couvre que le code : les données, contributions et modèles gardent leurs propres licences. |
| D11 | 2026-10-23 | Assistant (phase 3) : `claude-opus-5-5`, effort `medium`, repli serveur `fallbacks: "default"`, aucune conversation stockée. | Proposé, à valider | Modèle et effort modifiables par variables d'environnement ; tout changement impose une nouvelle passe d'évaluation. |

## Options étudiées pour la licence du code (tranché par D10)

| Option | Effet |
|---|---|
| **AGPL-3.0** (recommandée) | Toute version modifiée déployée comme service en ligne doit publier son code. Protège le mieux contre une appropriation fermée. |
| Apache-2.0 | Très permissive, avec clause de brevets ; permet des dérivés fermés. |
| MIT | La plus simple et la plus permissive. |

