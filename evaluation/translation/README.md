# Évaluation de la traduction

Protocole général : [docs/evaluation.md](../../docs/evaluation.md).

## Phrases de test (`sentences.jsonl`)

Les phrases et leurs **références sont écrites par des locuteurs**. Elles ne doivent jamais
servir à l'entraînement, à l'ajustement des consignes ni être importées dans le dictionnaire.

| Champ | Obligatoire | Contenu |
|---|---|---|
| `id` | oui | Identifiant unique |
| `source_lang`, `target_lang` | oui | `taq` avec `fr` ou `en`, dans un sens ou dans l'autre |
| `text` | oui | Phrase à traduire |
| `reference` | non | Traduction de référence par un locuteur (nécessaire au score chrF++) |
| `variant` | non | Variante du tamasheq |

Cible pour une première passe : **100 phrases par direction** (taq→fr, fr→taq, taq→en, en→taq),
de domaines variés (vie quotidienne, pastoralisme, santé, éducation…).

## Lancer

```bash
cd services/api
ANTHROPIC_API_KEY=... uv run python -m app.evaluation.translation_eval \
  ../../evaluation/translation/sentences.jsonl ../../evaluation/translation/results
# même passe sans le dictionnaire, pour mesurer son apport :
ANTHROPIC_API_KEY=... uv run python -m app.evaluation.translation_eval \
  ../../evaluation/translation/sentences.jsonl ../../evaluation/translation/results --no-glossary
```

Le script affiche le chrF++ par direction (sacrebleu, `word_order=2`) et écrit un CSV avec
chaque traduction, son chrF++ par phrase et les colonnes de notation.

**Coût estimé** (tarifs Anthropic au 2026-10, à revérifier) : environ 0,01 à 0,05 $ par phrase
avec `claude-opus-5-5`, soit 4 à 20 $ pour 400 phrases.

## Notation humaine (au moins 2 locuteurs par phrase)

| Colonne | Barème |
|---|---|
| `fidelite_0_2` | Le sens est-il rendu ? 0 non · 1 en partie · 2 oui |
| `grammaire_0_2` | 0 incorrecte · 1 erreurs mineures · 2 correcte |
| `naturel_0_2` | 0 artificiel · 1 compréhensible · 2 naturel |
| `orthographe_0_2` | Selon la convention retenue |
| `omissions_oui_non` | Une partie du texte manque-t-elle ? |
| `ajouts_oui_non` | Du contenu absent de l'original a-t-il été ajouté ? |
| `hallucinations_oui_non` | Mots inexistants ou faits inventés ? |
| `commentaire` | Correction proposée, variante |

Un score chrF++ seul ne prouve pas la qualité : il compare des caractères, pas le sens, et une
seule référence ne couvre pas les variantes légitimes.
