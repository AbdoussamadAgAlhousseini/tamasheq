# Évaluation des technologies vocales

> État au 2026-10-23 : **aucun modèle vocal n'a été exécuté ni évalué pour le tamasheq.**
> L'environnement de développement n'a pas accès à Hugging Face ni à l'index PyTorch ; les
> modèles candidats n'ont donc pas pu être téléchargés. Ce document fixe la méthode.

## Données de test

- Enregistrements **validés** de la plateforme, avec `allow_training = true` (l'évaluation est
  un usage par des modèles) et une transcription de référence validée par un locuteur.
- **Locuteurs distincts** entre entraînement éventuel et test ; noter la variante, l'âge
  approximatif (si consenti), le genre (si consenti) et les conditions (calme, bruit, extérieur,
  téléphone).
- Cible pour une première mesure : au moins 2 heures, 20 locuteurs, plusieurs variantes.
- Jeu complémentaire possible pour la recherche non commerciale : la partie test d'IWSLT2022
  (radio), **en évaluation seulement** (licence CC BY-NC-ND 3.0) et sans transcriptions
  tamasheq vérifiées à ce jour.

## Reconnaissance de la parole (ASR)

1. Exécuter le modèle candidat **hors de la plateforme** (machine avec GPU, accès à Hugging
   Face) sur les enregistrements de test.
2. Produire un fichier JSONL : `{"id", "reference", "hypothesis", "speaker", "condition"}`.
3. Calculer les scores :

```bash
cd services/api
uv run python -m app.evaluation.asr_eval resultats.jsonl
```

**WER** (erreurs sur les mots) et **CER** (erreurs sur les caractères), cumulés sur le
corpus, globalement et par locuteur et condition. Normalisation identique pour référence et
hypothèse : NFC, minuscules, ponctuation Unicode retirée, espaces réduits ; **diacritiques
conservés**. Le CER est souvent plus parlant que le WER pour une orthographe non stabilisée.

Candidats à comparer (licences à revérifier) :

| Modèle | Statut tamasheq | Licence | Remarque |
|---|---|---|---|
| Whisper | **non couvert** (vérifié) | MIT | écarté pour le tamasheq |
| MMS-1B-all (Meta) | `taq` à vérifier dans la liste des adaptateurs | CC BY-NC 4.0 | lectures religieuses dans les données d'entraînement (biais) |
| wav2vec 2.0 LIA tamasheq | pré-entraîné sur ≈234–243 h de radio | Apache-2.0 (à confirmer) | demande un affinage avec des transcriptions |

## Synthèse vocale (TTS)

- **Intelligibilité** : des locuteurs transcrivent des phrases synthétisées sans les voir ;
  calcul du CER entre la phrase d'origine et leur transcription.
- **Naturel et prononciation** : note de 1 à 5 par au moins 5 locuteurs, phrases mélangées
  avec des enregistrements réels (sans dire lesquels sont synthétiques).
- Aucune voix générique ou d'une autre langue n'est présentée comme une voix tamasheq.
- Une voix construite à partir d'une personne exige son accord explicite
  (`allow_voice_synthesis`), distinct de l'accord pour l'entraînement de la reconnaissance.

Candidat initial : MMS-TTS `taq` (listé, non vérifié, CC BY-NC 4.0).

## Pour lever le blocage

Autoriser `huggingface.co`, `*.hf.co` et `download.pytorch.org` dans l'environnement, ou
exécuter les modèles sur une machine dédiée, puis verser les fichiers de résultats ici.
