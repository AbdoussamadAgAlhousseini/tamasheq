# Évaluation de la recherche documentaire et des réponses citées

## 1. Recherche (sans modèle, gratuite)

Fichier `questions.jsonl`, une question par ligne, rédigée par des personnes qui connaissent
les documents :

```json
{"id": "k001", "question": "…", "relevant_document_ids": ["<uuid du document attendu>"]}
```

```bash
cd services/api
uv run python -m app.evaluation.retrieval_eval ../../evaluation/knowledge/questions.jsonl --k 6
```

Mesures : **rappel@6** (part des documents attendus parmi les passages qui seraient transmis au
modèle) et **MRR** (rang du premier document pertinent). Seuls les documents publics et validés
sont cherchés, comme pour les réponses. Si le rappel est insuffisant, comparer d'autres
méthodes (liste de mots-outils, recherche sémantique avec pgvector) sur ce même jeu.

## 2. Réponses (avec modèle)

Pour chaque question, des évaluateurs vérifient que :
- chaque affirmation de la réponse est soutenue par un passage cité (sinon : invention) ;
- la réponse signale « documentation insuffisante » quand les documents ne répondent pas ;
- aucun contenu d'un document non public n'apparaît.

Inclure des questions **sans réponse dans les documents** : la bonne réponse est alors un
signalement de documentation insuffisante, pas une réponse générale du modèle.
