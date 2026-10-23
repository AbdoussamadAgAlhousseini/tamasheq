# Recherche et sources — AKAL Tamasheq

> Statut : **Phase 0, version initiale** — date de vérification : 2026-10-23.
> Ce document ne contient aucune donnée tamasheq. Il recense des sources, ce qu'elles
> permettent et ce qu'elles ne permettent pas.

## Niveaux de vérification utilisés

| Code | Signification |
|---|---|
| **V1 — lu directement** | Le document (README, fichier, liste) a été ouvert et lu pendant la phase 0. |
| **V2 — vérifié indirectement** | Information obtenue par un moteur de recherche (extraits, notices bibliographiques), le document original n'ayant pas pu être ouvert. À relire avant toute décision engageante. |
| **V3 — à vérifier** | Source signalée ou supposée, non confirmée. Ne doit pas être utilisée comme fait. |

**Limite méthodologique importante :** l'environnement de travail de la phase 0 bloquait
l'accès direct à `aclanthology.org`, `arxiv.org`, `huggingface.co`, `commonvoice.mozilla.org`,
`gida-global.org` et `dl.fbaipublicfiles.com`. Seuls `github.com` / `raw.githubusercontent.com`
étaient accessibles directement. Les articles scientifiques n'ont donc **pas** été lus en texte
intégral : leurs résumés et métadonnées viennent de notices (V2). Une relecture intégrale est
une tâche ouverte (voir fin du document).

## Typologie des sources

- **[PR]** article évalué par les pairs (conférence ou revue)
- **[PP]** prépublication (arXiv) sans confirmation de publication évaluée
- **[DOC]** documentation officielle / fiche de modèle / README de dépôt
- **[COM]** ressource communautaire

---

## S1. Speech Resources in the Tamasheq Language — [PR] — V2

| Champ | Contenu |
|---|---|
| Auteurs | Marcely Zanon Boito, Fethi Bougares, Florentin Barbier, Souhir Gahbiche, Loïc Barrault, Mickael Rouvier, Yannick Estève |
| Année / lieu | 2022, Actes de LREC 2022, p. 2066–2071 |
| URL | https://aclanthology.org/2022.lrec-1.222/ — prépublication : https://arxiv.org/abs/2201.05051 |
| Résumé (reformulé) | Deux jeux de données vocaux : une collection non annotée de radio (≈671 h, 5 langues) et un corpus parallèle d'environ 17 h de parole tamasheq alignée au niveau de l'énoncé avec des traductions françaises. Sources : journaux radio de Studio Kalangou (Niger) et Studio Tamani (Mali). Publié pour la tâche « low-resource speech translation » d'IWSLT 2022. |
| Utile au projet | Seul corpus vocal tamasheq–français documenté scientifiquement trouvé à ce jour. Référence pour évaluer la traduction parole→texte et pour l'auto-apprentissage (wav2vec 2.0). |
| Limites | Domaine journalistique radio (≠ conversation quotidienne, savoirs, poésie). Locuteurs probablement peu nombreux et professionnels (journalistes) : à confirmer dans l'article. Répartition Mali/Niger des variantes à confirmer. Le corpus fournit des **traductions françaises**, pas (à notre connaissance, V3) de **transcriptions tamasheq** : il ne permet donc pas directement d'entraîner ou d'évaluer un ASR tamasheq→texte tamasheq. Un extrait indexé mentionne 5 829 énoncés (V3). |
| Licence | CC BY-NC-ND 3.0 (voir S2). |
| Décisions influencées | Ce corpus est classé « **évaluation et recherche uniquement** » tant qu'une autorisation écrite des ayants droit n'a pas été obtenue (voir S2). |

## S2. Dépôt `mzboito/IWSLT2022_Tamasheq_data` — [DOC] — V1

| Champ | Contenu |
|---|---|
| Organisme | LIA (Avignon Université) et partenaires ON-TRAC |
| URL | https://github.com/mzboito/IWSLT2022_Tamasheq_data |
| Contenu lu dans le README | `taq_fra_clean` : ≈17 h de parole tamasheq traduite en français. `taq_fra_full` : ≈19 h (ajoute ≈2 h jugées potentiellement bruitées par les annotateurs). Les deux versions **partagent les mêmes ensembles de validation et de test**. `taq_fra_clean` contient `train/`, `valid/`, `test/`. Audio non annoté (hébergé hors GitHub, `demo-lia.univ-avignon.fr/studios-tamani-kalangou/`) : français 116 h, fulfulde 114 h, haoussa 105 h, **tamasheq 234 h**, zarma 100 h. |
| Droits | « All audio recordings are property of Studio Kalangou, Studio Tamani and Fondation Hirondelle. » Licence : **Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported**. |
| Financement | ANR ON-TRAC (ANR-18-CE23-0021), Commission européenne SELMA (957017). |
| Écarts constatés | Total non annoté du README = 669 h ; l'article annonce 671 h. Les tailles des ensembles train/valid/test ne sont pas données dans le README. Formats de fichiers non décrits dans le README (à inspecter). |
| Analyse de licence (non juridique) | **NC** : aucune utilisation commerciale. **ND** : pas de diffusion d'œuvres dérivées. Le statut d'un modèle entraîné sur ces données au regard de la clause ND est **juridiquement incertain** ; la redistribution de segments modifiés (découpage, normalisation, réannotation) est exclue sans accord. L'accès public **n'est pas** une autorisation d'entraînement. |
| Décisions influencées | 1) Ne pas intégrer ces fichiers au dépôt AKAL. 2) Usage prévu limité à l'évaluation interne non commerciale, en citant la source. 3) Demande écrite à Fondation Hirondelle / LIA à envisager avant tout fine-tuning. 4) Le schéma de données AKAL doit porter licence et droits par enregistrement. |

## S3. `27Group/tamasheq_collection` (Hugging Face) — [COM] — V3

| Champ | Contenu |
|---|---|
| URL | https://huggingface.co/datasets/27Group/tamasheq_collection |
| Constat | Le dépôt apparaît dans la liste des datasets de l'organisation `27Group` (indexée par un moteur de recherche), avec une mention « 450k » dont la nature (lignes, téléchargements…) est inconnue. La fiche n'a **pas pu être lue** (accès bloqué). |
| Inconnu | Langues réelles, champs, volume, provenance, licence, présence de traductions automatiques, doublons, lien éventuel avec S1/S2. |
| Décision | **Aucune utilisation** avant lecture de la fiche, vérification de la licence et audit d'un échantillon par des locuteurs (est-ce bien du tamasheq ? quelle variante ? texte authentique ou généré ?). |

Autres dépôts Hugging Face repérés, **non examinés** (V3) : `YassineBenlaria/tamasheq_data` (dataset),
`ad019el/Tamasheq-XLSR-53-mixed-Kabyle` (modèle), collection `Tamazight-NLP/bitext-datasets`
(attention : tamazight ≠ tamasheq).

## S4. Mozilla Common Voice — [DOC] — V3

| Champ | Contenu |
|---|---|
| URL | https://commonvoice.mozilla.org/fr/datasets ; https://www.mozillafoundation.org/en/common-voice/platform-and-dataset/ |
| Constat | Aucune preuve trouvée d'un corpus Common Voice en tamasheq (`taq`). Les pages officielles n'ont pas pu être consultées. Un article sur les contributions tamazight à Common Voice (« Awal », arXiv 2510.27407, [PP], V2) mentionne le tamasheq seulement comme langue parlée au Mali et au Niger. |
| Vigilance | Les corpus Common Voice de langues amazighes (ex. kabyle, tamazight) **ne sont pas** du tamasheq et ne doivent pas être utilisés comme tel. |
| Utile au projet | Modèle de collecte (phrases lues, validation croisée par d'autres contributeurs, licence CC0 des enregistrements). La licence CC0 est **incompatible** avec des savoirs restreints : une collecte AKAL doit séparer phrases publiques (pouvant éventuellement aller vers Common Voice) et contenus communautaires gouvernés. |
| Décision | Étudier, avec les communautés, une contribution à Common Voice pour des phrases neutres ; ne jamais y verser de savoirs sensibles. |

Ressource voisine : demande d'ajout du tamasheq à Tatoeba (issue GitHub `Tatoeba/tatoeba2#3351`, V2).

## S5. Masakhane — [COM] + [PR] — V2

| Champ | Contenu |
|---|---|
| URL | https://www.masakhane.io/ ; https://github.com/masakhane-io/masakhane-community |
| Publication clé | Nekoto et al. (communauté Masakhane), « Participatory Research for Low-resourced Machine Translation: A Case Study in African Languages », Findings of EMNLP 2020, p. 2144–2160, DOI 10.18653/v1/2020.findings-emnlp.195 [PR] |
| Résultats utiles | La « faible dotation » dépasse le manque de données : il faut impliquer locuteurs, traducteurs, évaluateurs. Jeux de données et benchmarks MT pour 30+ langues africaines, évaluation humaine pour environ un tiers. |
| Limites | Aucun travail tamasheq identifié dans les résultats consultés (à vérifier dans le dépôt communautaire). Les résultats d'autres langues ne se transposent pas au tamasheq. |
| Décisions | Approche participative ; prise de contact possible avec la communauté ; protocole d'évaluation humaine inspiré de leurs pratiques. |

## S6. Whisper (OpenAI) — [DOC] — V1

| Champ | Contenu |
|---|---|
| URL | https://huggingface.co/docs/transformers/model_doc/whisper ; code : https://github.com/openai/whisper |
| Vérification | Lecture de `whisper/tokenizer.py` (branche `main`, 2026-10-23) : la liste des langues **ne contient ni le tamasheq (`taq`) ni aucune langue amazighe**. |
| Conséquence | Whisper ne peut pas produire de transcription tamasheq « nativement ». Un fine-tuning serait nécessaire et suppose des transcriptions tamasheq que nous n'avons pas (voir S1). Whisper pourrait servir à transcrire le **français** des traductions ou des explications. |

## S7. NLLB-200 et FLORES-200 (Meta) — [PP] + [DOC] — V1/V2

| Champ | Contenu |
|---|---|
| URL | Article : https://arxiv.org/abs/2207.04672 (« No Language Left Behind », NLLB Team, 2022). FLORES-200 : https://github.com/facebookresearch/flores |
| V1 | Le README FLORES-200 liste **`taq_Latn` (Tamasheq, écriture latine)** et **`taq_Tfng` (Tamasheq, tifinagh)**. |
| V2 | Les fiches de modèles NLLB-200 (600M distillé, 1.3B, 3.3B…) incluent ces codes. Licence des modèles : **CC BY-NC 4.0** (non commerciale). Métriques de l'article : chrF++ (principale) et spBLEU sur FLORES-200 devtest. |
| Inconnu | Scores `taq_*` publiés dans les annexes (non récupérés). Qualité et variante du texte FLORES `taq_*` (à faire juger par des locuteurs). |
| Décision | Premier candidat pour la **traduction expérimentale** et pour la translittération de référence ; à évaluer sur un jeu de test AKAL indépendant. Licence NC : à arbitrer selon le modèle économique. |

## S8. MMS — Massively Multilingual Speech (Meta) — [PP] + [DOC] — V2

| Champ | Contenu |
|---|---|
| URL | Pratap et al., « Scaling Speech Technology to 1,000+ Languages », https://arxiv.org/abs/2305.13516 ; https://github.com/facebookresearch/fairseq/tree/main/examples/mms |
| V1 | README fairseq : ASR (MMS-1B-all, 1 162 langues), TTS VITS par langue (≈1 100 langues), identification de langue (jusqu'à 4 017). |
| V2 | La liste de langues TTS (`all_langs.tsv` de l'espace `mms-meta/MMS`) contient « taq Tamasheq ». Présence de `taq` dans MMS-1B-all **non confirmée**. Licence : CC BY-NC 4.0. |
| Limite à vérifier | D'après l'article, les données étiquetées MMS proviennent largement de lectures de textes religieux (à relire) : biais de domaine, de registre, de locuteur et de variante probables. |
| Décision | Candidat à **évaluer** pour la TTS et l'ASR. Une voix MMS ne doit pas être présentée comme une « voix tamasheq naturelle » avant jugement par des locuteurs. |

## S9. Systèmes IWSLT tamasheq→français — [PR] — V2

| Travail | Résultat rapporté |
|---|---|
| Findings IWSLT 2022 (2022.iwslt-1.10) | Meilleur BLEU (SacreBLEU, minuscules) **5,7**, système ON-TRAC ; 3 équipes. |
| ON-TRAC 2022 (arXiv 2205.01987) | Bout-en-bout avec représentations wav2vec 2.0 pré-entraîné sur ≈234 h de tamasheq. |
| NAVER LABS Europe, IWSLT 2023 (arXiv 2306.07763) | **23,6 BLEU** sur le test 2023 (selon leurs auteurs). |
| Amazon, IWSLT 2023 (2023.iwslt-1.21) | Augmentation de données et ensembles ; note que les LLM manquaient de données tamasheq pour générer des transcriptions synthétiques. |

Enseignement : la traduction parole→français reste difficile ; un BLEU de cet ordre ne permet
pas une traduction fiable en production. Ces scores portent sur le domaine radio uniquement.

## S10. Modèles wav2vec 2.0 du LIA — [DOC] — V2

`LIA-AvignonUniversity/IWSLT2022-tamasheq-only` et `LIA-AvignonUniversity/IWSLT2022-Niger-Mali`.
La fiche Niger-Mali indique une licence **Apache-2.0** pour les modèles pré-entraînés et 243 h de
tamasheq (l'article ON-TRAC dit 234 h : écart à clarifier). La fiche « tamasheq-only » est
quasiment vide (licence non vérifiée). Point juridique ouvert : relation entre la licence
Apache-2.0 du modèle et la licence ND des données d'entraînement.
Décision : candidat sérieux comme **encodeur acoustique** pour un futur ASR, sous réserve de
clarification des droits.

## S11. Écriture tifinagh et Unicode — [DOC] — V2

- Bloc Unicode Tifinagh : U+2D30–U+2D7F ; répertoire fondé sur le néo-tifinagh avec des
  caractères ajoutés pour le touareg.
- Unicode Technical Note #59 (https://www.unicode.org/notes/tn59/) : classe le tamasheq (`taq`)
  et le tawallammat (`ttq`) parmi les langues utilisant le tifinagh traditionnel.
- Conséquence : le tifinagh touareg traditionnel (souvent sans voyelles, ligatures, variantes
  régionales) **ne correspond pas** caractère par caractère à l'orthographe latine. La conversion
  doit être un module de règles versionnées par convention, validé par des locuteurs.
- ISO 639-3 apparentés (à vérifier sur le registre SIL) : `taq` (tamasheq), `ttq` (tawallammat),
  `thv` (tahaggart), `thz` (tayart). Le périmètre « tamasheq » d'AKAL doit être défini avec les
  communautés.

## S12. Principes CARE — [PR] — V2

Carroll S. R. et al., « The CARE Principles for Indigenous Data Governance », *Data Science
Journal* 19, 2020, DOI 10.5334/dsj-2020-043. Site : https://www.gida-global.org/care.
CARE = **C**ollective benefit, **A**uthority to control, **R**esponsibility, **E**thics ;
complémentaires aux principes FAIR (« Be FAIR and CARE »). Élaborés par l'International
Indigenous Data Sovereignty Interest Group (Research Data Alliance).
Décisions : consentement individuel **et** collectif, autorité communautaire sur l'accès,
retrait possible, niveaux d'accès, bénéfice explicite pour les communautés.

## S13. TifinaghBench — [COM] — V2

https://github.com/Itri-Cloud-Labs/TifinaghBench : banc d'essai communautaire de vocabulaire
amazigh en tifinagh pour LLM. **Ne couvre pas le tamasheq** d'après les extraits consultés.
Intérêt : méthode (questions à livre fermé, CER sur réponses exactes) réutilisable pour un
banc d'essai tamasheq.

## S14. Grands modèles de langage généralistes — V3

Aucune évaluation publiée des capacités en tamasheq des modèles généralistes (Claude, GPT,
Gemini, Llama, Gemma, Qwen, Aya…) n'a été trouvée. **Hypothèse de travail : leur compétence en
tamasheq est inconnue et probablement faible.** Elle sera mesurée par le protocole
`evaluation/` avant toute mise en avant.

---

## Tâches de vérification ouvertes

1. Lire en texte intégral S1, S7 (annexes `taq_*`), S8 (liste des langues ASR, données), S9.
2. Ouvrir la fiche et un échantillon de `27Group/tamasheq_collection` et `YassineBenlaria/tamasheq_data`.
3. Inspecter les formats et tailles des fichiers de S2 ; confirmer l'absence de transcriptions tamasheq.
4. Vérifier la liste des langues Common Voice.
5. Lire le texte intégral de CARE et rechercher la littérature sur le consentement collectif.
6. Rechercher les dictionnaires et lexiques tamasheq publiés (ex. travaux lexicographiques sur le tamasheq du Mali) **avec leurs droits** — non traité en phase 0.
7. Identifier les institutions maliennes concernées par la normalisation de l'orthographe tamasheq.

Pour lever les blocages, autoriser dans l'environnement : `huggingface.co`, `*.hf.co`,
`aclanthology.org`, `arxiv.org`, `commonvoice.mozilla.org`, `gida-global.org`,
`dl.fbaipublicfiles.com`, `unicode.org`.
