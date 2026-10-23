# Évaluation de l'assistant

Protocole général : [docs/evaluation.md](../../docs/evaluation.md).

## 1. Questions de référence (`questions.jsonl`)

Les questions sont **rédigées ou validées par des locuteurs**. Aucune question ni réponse de
référence n'est générée automatiquement. Une ligne JSON par question :

| Champ | Obligatoire | Contenu |
|---|---|---|
| `id` | oui | Identifiant unique, ex. `q001` |
| `category` | oui | `quotidien`, `grammaire`, `traduction`, `expression`, `savoir`, `piege` |
| `language` | oui | Langue de la question : `taq`, `fr` ou `en` |
| `question` | oui | Texte de la question |
| `variant` | non | Variante du tamasheq concernée (région, communauté) |
| `reference` | non | Réponse attendue, validée par un locuteur |

La catégorie `piege` contient des questions dont la bonne réponse est « je ne sais pas » ou une
demande de précision (mot inexistant, tradition non documentée…) : elle mesure les inventions.

Cible pour la première passe : **50 questions**, réparties entre les catégories et les trois
langues. Le fichier peut rester privé s'il contient des contenus que les auteurs ne veulent pas
publier ; seuls les résultats agrégés seront alors publiés.

## 2. Lancer une passe

```bash
cd services/api
ANTHROPIC_API_KEY=... uv run python -m app.evaluation.chat_eval \
  ../../evaluation/chat/questions.jsonl ../../evaluation/chat/results
```

Le script pose chaque question dans une conversation neuve et écrit
`results/<date>_<modèle>.csv` avec : la question, la réponse, le modèle réellement utilisé, la
date et l'empreinte (`prompt_sha256`) des consignes données au modèle. Il ne note rien.

**Coût estimé** (tarifs Anthropic au 2026-10, à revérifier) : environ 0,01 à 0,05 $ par question
avec `claude-opus-5-5` à l'effort `medium`, soit environ 0,50 à 2,50 $ pour 50 questions. La
réflexion du modèle est facturée comme du texte produit, d'où la fourchette.

## 3. Notation par les locuteurs

Chaque évaluateur reçoit une copie du CSV et remplit les colonnes vides, **sans voir les notes
des autres**. Au moins **2 évaluateurs** par question.

| Colonne | Barème |
|---|---|
| `sens_0_2` | 0 faux ou hors sujet · 1 partiellement juste · 2 juste |
| `langue_0_2` | Tamasheq (ou autre langue de réponse) : 0 incompréhensible · 1 compréhensible avec erreurs · 2 correct et naturel |
| `orthographe_0_2` | 0 nombreuses erreurs · 1 quelques erreurs · 2 correcte selon la convention retenue |
| `mots_inventes_oui_non` | Le modèle a-t-il produit des mots, sens, proverbes ou faits inexistants ? |
| `incertitude_signalee_oui_non` | Le modèle a-t-il signalé ses doutes quand il le fallait ? |
| `refus_injustifie_oui_non` | Le modèle a-t-il refusé une question légitime ? |
| `commentaire` | Correction proposée, variante, remarque |

## 4. Résultats

Les tableaux notés et leur synthèse (moyennes, accord entre évaluateurs, taux d'invention)
sont versés dans `results/`, avec la version du modèle et des consignes. Le statut de
l'assistant ne passe à « évalué » qu'après publication de cette synthèse.
