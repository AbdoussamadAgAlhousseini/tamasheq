# Rapport de phase 0 — audit, recherche et cadrage

> Date : 2026-10-23. Statut : **proposition soumise à validation**. Aucune décision structurante
> n'est considérée comme prise tant qu'elle n'est pas validée par le porteur du projet.
> Références `S1…S14` : voir [research-and-sources.md](research-and-sources.md).

## 1. État des lieux de l'environnement

| Élément | Constat |
|---|---|
| Contenu existant | Aucun code TAMASHEQ préexistant. Le dépôt ouvert dans la session (`AbdoussamadAgAlhousseini.github.io`, site OMPIDES) n'est pas concerné. Le projet est préparé comme un **nouveau dépôt** `tamasheq`. |
| Outils | Python 3.13, uv 0.11, Node 22, npm 10, pnpm 10, Docker 29, PostgreSQL 16 (client `psql`), ffmpeg 6.1, git 2.43. |
| Matériel | 4 vCPU, 15 Go RAM, **pas de GPU**. |
| Réseau | Accès bloqué à Hugging Face, arXiv, ACL Anthology, Common Voice, GIDA, serveurs Meta. GitHub accessible. Téléchargement de modèles impossible pour l'instant. |
| GitHub | La création automatique du dépôt a été refusée (droits de l'intégration). Le dépôt doit être créé manuellement. |

Conséquence : la phase 0 a pu produire la recherche et le cadrage, **pas** d'évaluation
expérimentale de modèles. Aucun résultat de modèle n'est donc rapporté.

## 2. Tableau des jeux de données

| Jeu | Contenu | Volume | Licence | Entraînement autorisé ? | Utilité | Vérif. |
|---|---|---|---|---|---|---|
| IWSLT2022 `taq_fra_clean` (S1, S2) | Parole tamasheq (radio) + traduction française | ≈17 h | CC BY-NC-ND 3.0, propriété Studio Kalangou / Studio Tamani / Fondation Hirondelle | **Non établi** (ND + NC) ; accord écrit requis | Évaluation parole→français ; référence scientifique | V1 |
| IWSLT2022 `taq_fra_full` | Idem + ≈2 h potentiellement bruitées | ≈19 h | Idem | Idem | Idem | V1 |
| Audio non annoté (S2) | Radio tamasheq sans texte | 234 h | Idem | Idem | Pré-entraînement auto-supervisé (déjà fait par le LIA, S10) | V1 |
| FLORES-200 `taq_Latn`, `taq_Tfng` (S7) | Phrases traduites de l'anglais (Wikipédia) | ≈3 000 phrases par langue (benchmark complet) | Licence du dépôt FLORES à relire | Non — réservé à l'évaluation | Test de traduction texte, comparaison latin/tifinagh | V1 (codes) / V3 (licence, qualité) |
| `27Group/tamasheq_collection` (S3) | Inconnu | Inconnu | Inconnue | Inconnu | À auditer | V3 |
| `YassineBenlaria/tamasheq_data` | Inconnu | Inconnu | Inconnue | Inconnu | À auditer | V3 |
| Common Voice (S4) | Aucun corpus tamasheq trouvé | — | CC0 pour les corpus existants | — | Modèle méthodologique de collecte | V3 |
| Contributions TAMASHEQ futures | Texte, audio, dictionnaire, savoirs | 0 aujourd'hui | Définie par contribution | Selon consentement explicite et séparé | **Source principale à terme** | — |

**Constat central :** il n'existe à notre connaissance **aucun corpus tamasheq librement
réutilisable pour l'entraînement**, ni corpus de transcriptions tamasheq pour l'ASR. La
constitution d'un corpus communautaire gouverné est donc le cœur du projet, pas un à-côté.

## 3. Modèles candidats

| Fonction | Candidats | Couverture tamasheq | Licence | Besoins matériels | Statut |
|---|---|---|---|---|---|
| Conversation | API généralistes (Claude, GPT, Gemini) ; modèles ouverts (Llama, Gemma, Qwen, Aya…) | **Inconnue**, aucune évaluation publiée (S14) | Conditions commerciales / licences propres à chaque modèle, à comparer | API : aucun GPU ; modèles ouverts : GPU pour les tailles utiles | À évaluer |
| Traduction | NLLB-200 (600M distillé, 1.3B, 3.3B) | `taq_Latn` et `taq_Tfng` déclarés (S7) | CC BY-NC 4.0 | 600M distillé : faisable sur CPU pour l'évaluation | Candidat n°1 à évaluer |
| Traduction | LLM généralistes | Inconnue | Variable | API | À comparer à NLLB |
| ASR | Whisper | **Non couvert** (V1, S6) | MIT | — | Écarté pour le tamasheq (utile pour le français) |
| ASR | MMS-1B-all + adaptateur | `taq` non confirmé (S8) | CC BY-NC 4.0 | 1B paramètres, CPU lent | À vérifier puis évaluer |
| ASR / ST | wav2vec 2.0 LIA tamasheq (S10) | Pré-entraîné sur ≈234–243 h de tamasheq | Apache-2.0 (Niger-Mali, V2) | Fine-tuning : GPU | Meilleur encodeur candidat, nécessite des transcriptions |
| TTS | MMS-TTS `taq` (VITS) | Listé (V2) | CC BY-NC 4.0 | Léger, CPU possible | À faire juger par des locuteurs |
| TTS | Voix TAMASHEQ dédiée (VITS ou équivalent) | — | Propre, avec consentement des voix | GPU pour l'entraînement | Phase 6–7, si données consenties |

Règle : un modèle ne sera mis en avant pour une fonction qu'après un score reproductible sur
le jeu de test TAMASHEQ et un jugement humain favorable.

## 4. Faits vérifiés et éléments à confirmer

**Vérifiés (V1)**
- Le corpus IWSLT2022 tamasheq–français existe (≈17 h propre, ≈19 h complet, valid/test communs) sous CC BY-NC-ND 3.0, avec 234 h d'audio tamasheq non annoté.
- FLORES-200 contient `taq_Latn` et `taq_Tfng`.
- Whisper ne liste pas le tamasheq.

**Vérifiés indirectement (V2)** : métadonnées des articles S1, S5, S9, S12 ; licences NC de NLLB et MMS ; présence de `taq` dans la TTS MMS ; scores IWSLT (5,7 BLEU en 2022 ; 23,6 annoncé par NAVER en 2023).

**À confirmer (V3)** : contenu et licence des datasets Hugging Face ; absence de transcriptions tamasheq dans IWSLT2022 ; `taq` dans MMS-1B-all ; scores NLLB `taq_*` ; absence du tamasheq dans Common Voice ; compétence des LLM en tamasheq ; conventions orthographiques en usage au Mali.

## 5. Architecture technique proposée

```
                 ┌──────────────── Navigateur / mobile ────────────────┐
                 │ Next.js (React, TypeScript, Tailwind) — apps/web    │
                 └───────────────┬─────────────────────────────────────┘
                                 │ HTTPS (REST, JSON)
                 ┌───────────────▼─────────────────────────────────────┐
                 │ API FastAPI + Pydantic — services/api               │
                 │ auth, rôles, permissions, limitation, journal       │
                 │ ┌──────────┬───────────┬────────┬──────┬─────────┐  │
                 │ │ chat     │ translate │ search │ asr  │ tts     │  │ interfaces IA
                 │ └────┬─────┴─────┬─────┴───┬────┴──┬───┴────┬────┘  │
                 │      └─ adaptateurs fournisseurs (API, local, worker)│
                 └──────┬──────────────┬──────────────┬────────────────┘
                        │              │              │
               PostgreSQL 16     Stockage objet     Workers ML (option GPU,
               (Alembic)         S3-compatible      à la demande) — services/ml
                                 (audio)
```

Justifications :
- **Séparation front / API / ML** : les besoins de calcul de la voix et de la traduction locale sont incompatibles avec un hébergement web classique ; les workers ML peuvent tourner ailleurs (GPU loué ponctuellement) sans toucher au reste.
- **Adaptateurs de fournisseurs** : une interface Python par fonction (`ChatProvider`, `TranslationProvider`, `AsrProvider`, `TtsProvider`, `Retriever`) ; chaque réponse porte `provider`, `model`, `version` et `status` (`experimental` / `evaluated`). Permet de changer de fournisseur sans réécrire l'application et de tracer quel modèle a produit quoi.
- **PostgreSQL** pour la provenance, les licences, le consentement et l'historique des corrections (relations fortes, transactions). **pgvector** seulement si la recherche lexicale (texte intégral + normalisation) se révèle insuffisante.
- **Normalisation et translittération** comme bibliothèque Python pure, versionnée par convention orthographique, testée par jeux d'exemples validés ; jamais appliquée de façon destructive au texte source (on stocke l'original et des formes dérivées).
- **Monorepo** : `apps/web`, `services/api`, `services/ml`, `packages/script-tools`, `evaluation/`, `docs/`, `infra/` (docker compose local avec PostgreSQL et MinIO).

## 6. Coûts, contraintes matérielles et risques

**Coûts principaux (à chiffrer avec des devis, aucun montant avancé ici)**
- Rémunération des locuteurs, transcripteurs, traducteurs et réviseurs : **poste dominant**, et condition éthique.
- Appels d'API LLM : proportionnels à l'usage ; plafonds par utilisateur nécessaires.
- GPU ponctuel pour fine-tuning ASR/TTS (phases 6–7 seulement).
- Hébergement : front, API, base PostgreSQL managée, stockage audio, sauvegardes.
- Conseil juridique (licences ND/NC, protection des données, droit malien).

**Risques**

| Risque | Gravité | Mesure |
|---|---|---|
| Hallucinations en tamasheq présentées comme fiables | Élevée | Étiquetage « expérimental », évaluation préalable, affichage des sources, correction communautaire |
| Licences non commerciales (NLLB, MMS, IWSLT) incompatibles avec un futur modèle économique | Élevée | Décision explicite sur le caractère commercial ou non ; alternatives à licence permissive |
| Clause ND du corpus IWSLT | Élevée | Pas d'entraînement ni redistribution sans accord écrit |
| Confusion tamasheq / tamazight ou entre variantes | Moyenne | Codes ISO et variante obligatoires sur chaque donnée ; revue par locuteurs |
| Savoirs sensibles exposés via le RAG ou l'entraînement | Élevée | Filtrage par permissions **avant** la récupération ; drapeau d'entraînement distinct |
| Sécurité des contributeurs (contexte sécuritaire au Mali) | Élevée | Pseudonymisation par défaut, minimisation des métadonnées, géolocalisation fine interdite par défaut |
| Connexions lentes / coût des données mobiles | Moyenne | Pages légères, audio compressé (Opus), mode dégradé |
| Dépendance à un fournisseur d'IA | Moyenne | Adaptateurs, export des données, pas de données restreintes envoyées aux API externes sans accord |

## 7. Plan de développement et critères d'acceptation

| Phase | Livrables | Critères d'acceptation |
|---|---|---|
| 0 — Audit (en cours) | Ce rapport, `research-and-sources.md` | Validation écrite du porteur sur les décisions D1–D8 ci-dessous |
| 1 — Fondations | Monorepo, Next.js, FastAPI, PostgreSQL + Alembic, docker compose, CI (lint, types, tests), `.env.example`, docs d'installation | `docker compose up` démarre tout ; CI verte ; migration initiale réversible ; aucun secret dans le dépôt |
| 2 — Interface | 9 pages, navigation, sélecteur d'écriture et de langue, états chargement/erreur | Lighthouse accessibilité ≥ 90 ; affichage tifinagh correct sur Android/iOS testés ; utilisable à 360 px de large |
| 3 — Premier assistant | Adaptateur LLM côté serveur, limitation, gestion d'erreurs, bannière « capacité non vérifiée » | Clés jamais exposées (test) ; délais et pannes gérés ; jeu de 50 questions de référence évalué par au moins 2 locuteurs, résultats publiés |
| 4 — Corpus et dictionnaire | Schéma de données (provenance, consentement, licence, statuts brut/en attente/validé/restreint/retiré), import/export, validation, historique | Retrait d'une contribution propagé et tracé ; aucune entrée « validée » sans réviseur ; tests de normalisation |
| 5 — Traduction et RAG | Traducteur expérimental (NLLB et/ou LLM), RAG filtré par permissions avec citations | chrF++ et évaluation humaine sur jeu de test TAMASHEQ ; test prouvant qu'un document restreint n'est jamais récupéré pour un utilisateur non autorisé |
| 6 — Voix | Enregistrement navigateur, correction de transcriptions, évaluation MMS/wav2vec | WER/CER publiés avec normalisation documentée ; TTS jugée par locuteurs avant mise en ligne |
| 7 — Spécialisation | Jeux de données autorisés, comparaison d'adaptations (LoRA, fine-tuning) | Gain mesuré sur test isolé, sans fuite ; coût justifié |
| 8 — Bêta | Audit de sécurité, sauvegardes testées, documentation des limites | Restauration testée ; retours de locuteurs intégrés avant diffusion large |

## 8. Décisions nécessitant votre validation

> **Mise à jour 2026-10-23 :** réponses consignées dans [decisions.md](decisions.md).

- **D1. Dépôt** : nom `tamasheq`, **privé** au départ ? (recommandé : privé jusqu'à la mise en place de la gouvernance)
- **D2. Caractère commercial** : TAMASHEQ est-il strictement non commercial ? Cela conditionne l'usage de NLLB, MMS et IWSLT (tous NC).
- **D3. Périmètre linguistique** : quelles variantes en priorité (tamasheq du Mali : quelles régions ?), et quels codes ISO couvrir (`taq` seul, ou aussi `ttq`, `thv`, `thz`) ?
- **D4. Conventions orthographiques** : quelle convention latine et quel tifinagh comme formes de référence initiales (sans exclure les autres) ? Qui sont les réviseurs habilités ?
- **D5. Gouvernance** : quelle instance communautaire valide l'accès aux savoirs restreints et les retraits ?
- **D6. Fournisseur LLM initial** pour la phase 3, et accepte-t-on d'envoyer des textes publics à une API externe ?
- **D7. Hébergement** : contraintes de localisation des données (Mali, Afrique, Europe) ?
- **D8. Contacts** : faut-il solliciter le LIA / Fondation Hirondelle (droits IWSLT) et Masakhane ?
