# Constitution des corpus

> Aucune donnée tamasheq n'est livrée avec le projet. Ce document décrit comment en ajouter,
> avec leur provenance et leurs droits.

## Ce qui n'entre jamais dans le corpus

- Des textes ou traductions **générés automatiquement** présentés comme authentiques.
- Des données dont la licence ne permet pas l'usage prévu. Exemple : le corpus IWSLT2022
  (CC BY-NC-ND 3.0) est réservé à l'évaluation, sans import ni redistribution (voir
  [research-and-sources.md](research-and-sources.md)).
- Des savoirs restreints sans l'autorisation des personnes ou communautés concernées.

## Procédure d'import

```bash
cd services/api
# 1. Déclarer la source et ses droits (--training : yes | no | unknown)
uv run python -m app.cli add-source --title "…" --kind dictionary \
  --license "…" --training unknown --citation "…"
# 2. Importer (tout ou rien ; statut « brut »)
uv run python -m app.cli import lexicon entrees.jsonl --source <id> --actor moi@exemple.org
# 3. Faire valider par des réviseurs (API : POST /api/v1/dictionary/{id}/validate)
# 4. Exporter
uv run python -m app.cli export lexicon --purpose publication --name lexique-v1 --out exports/
```

Le fichier entier est vérifié avant toute écriture ; en cas d'erreur, chaque ligne fautive est
signalée et rien n'est importé.

## Format : dictionnaire (`import lexicon`)

Une entrée JSON par ligne.

| Champ | Obligatoire | Contenu |
|---|---|---|
| `headword` | oui | Forme d'entrée, telle que dans la source (jamais modifiée ensuite) |
| `script` | non | `Latn` ou `Tfng` ; détecté automatiquement, refusé si incohérent ou mélangé |
| `spellings` | non | Autres graphies : `[{"form": "…", "script": "Tfng"}]` |
| `senses` | oui | Au moins un sens : `definition_fr`, `definition_en`, `translation_fr`, `translation_en` (au moins un des quatre), `examples` (`text`, `translation_fr`, `translation_en`) |
| `part_of_speech` | non | Catégorie grammaticale si la source la donne |
| `variant` | non | Variante (région, communauté) |
| `language` | non | Code ISO 639-3, `taq` par défaut |
| `license` | oui | Licence ou régime de droits de l'entrée |
| `allow_publication` | oui | `true` / `false` |
| `allow_training` | oui | `true` / `false` |
| `consent_reference` | non | Référence du consentement (formulaire, enregistrement) |
| `distribution_restrictions` | non | Restrictions de diffusion (exclut des exports automatiques) |
| `collected_on` | non | Date de collecte `AAAA-MM-JJ` |
| `notes` | non | Remarques |

## Format : corpus de textes (`import corpus`)

Mêmes champs de droits, plus : `text` (obligatoire, texte original), `script`,
`tifinagh_text` (forme tifinagh validée, entièrement en tifinagh), `translation_fr`,
`translation_en`, `notes`.

## Format : bibliothèque des savoirs (`import knowledge`)

Mêmes champs de droits, plus : `title`, `body` (texte intégral, paragraphes séparés par une
ligne vide ; jamais modifié ensuite), `theme` (`oral_history`, `proverbs`, `culture`,
`pastoralism`, `environment`, `plants`, `toponymy`, `crafts`, `intergenerational`,
`language`), `access_level` (`public`, `community`, `restricted`), `author_credit` (seulement
si la personne accepte d'être nommée), `language` (code ISO 639-3 du document, `fra` par défaut).

Le niveau d'accès est décidé **avec les personnes et communautés concernées** avant l'import.

## Contribution directe par l'API

```bash
curl -X POST https://<api>/api/v1/dictionary \
  -H "Authorization: Bearer <jeton>" -H "Content-Type: application/json" \
  -d '{"headword": "…", "senses": [{"translation_fr": "…"}], "license": "CC-BY-4.0",
       "allow_publication": true, "allow_training": false}'
```

La contribution arrive « en attente » et doit être validée par un autre réviseur.

## Normalisation

Seules des opérations Unicode sont appliquées : composition NFC et espaces. La recherche
ignore la casse mais **conserve les diacritiques** (ḍ ≠ d, ɣ ≠ g), car les confondre serait une
décision linguistique. Les règles propres au tamasheq (équivalences, conversion latin ↔
tifinagh) seront définies par convention (`add-convention`) et validées par des locuteurs ;
aucune conversion automatique n'est faite.
