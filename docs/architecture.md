# Architecture

Justification détaillée : [phase-0-report.md §5](phase-0-report.md#5-architecture-technique-proposée).

## Arborescence

```
apps/web/          Frontend Next.js 16 (React 19, TypeScript, Tailwind CSS 4)
services/api/      API FastAPI (Python 3.13, SQLAlchemy 2, Alembic, Pydantic)
  app/             code de l'application
  migrations/      migrations Alembic versionnées
  tests/           tests pytest
infra/             docker compose de développement (PostgreSQL 16)
evaluation/        (phase 3+) jeux de test, scripts, résultats
docs/              documentation
```

Prévus plus tard : `services/ml/` (workers ASR, TTS et traduction locale), `packages/script-tools/`
(normalisation latin/tifinagh).

## Frontend (état actuel)

| Route | Contenu |
|---|---|
| `/` | Présentation, modules et leur état, engagements |
| `/chat`, `/translate`, `/dictionary`, `/knowledge`, `/voice` | Ce qui est prévu, limites et garanties, état réel du module (lu depuis l'API) |
| `/contribute` | Contributions prévues et droits des contributeurs (contributions pas encore ouvertes) |
| `/admin` | Espace réservé, non indexé ; aucune action possible tant que l'authentification n'existe pas |
| `/about` | Vision, gouvernance (CARE), écritures, sources |

Choix techniques :

- **Pas de fonctionnalité fictive** : aucune page n'offre de saisie qui ne ferait rien. L'état de
  chaque module vient de `GET /api/v1/capabilities` ; si l'API est injoignable, l'interface
  affiche « état inconnu », jamais « disponible ».
- **Langue d'interface (FR/EN)** : les deux textes sont dans le HTML (`components/T.tsx`) et la
  feuille de style masque la langue non choisie. Un script en ligne applique la préférence
  enregistrée avant le premier affichage : pas de clignotement, pages entièrement statiques,
  attribut `lang` correct pour les lecteurs d'écran. L'interface en tamasheq viendra avec des
  traductions validées par des locuteurs.
- **Écriture tamasheq (latin/tifinagh)** : préférence enregistrée (`data-script` sur `<html>`),
  qui s'appliquera aux contenus tamasheq validés (phase 4).
- **Police tifinagh** : Noto Sans Tifinagh (OFL-1.1), auto-hébergée dans `public/fonts/`, avec
  `unicode-range` : elle n'est téléchargée que si la page contient du tifinagh (≈18 Ko).
- Préférences stockées dans `localStorage` uniquement, aucune donnée envoyée au serveur.

## API (état actuel)

| Route | Rôle |
|---|---|
| `GET /health` | État de l'API et de la base (503 si la base est indisponible) |
| `GET /api/v1/capabilities` | Liste des fonctions et de leur statut (`not_available`, `experimental`, `evaluated`). Toutes sont `not_available` en phase 1. |
| `GET /docs` | Documentation OpenAPI générée |

L'endpoint `capabilities` est la source de vérité de ce que l'interface affiche comme
disponible : l'interface ne doit pas annoncer une fonction que l'API déclare indisponible.

## Base de données

Migration `0001` : table `users` (pseudonyme public, e-mail privé, rôle `contributor` /
`reviewer` / `admin`). Aucune donnée d'authentification n'est stockée tant que la méthode
d'authentification n'est pas choisie. Les schémas du corpus, du dictionnaire, du consentement
et des licences arrivent en phase 4.

## Lancement local

Prérequis : Node 22, Python 3.13, [uv](https://docs.astral.sh/uv/), PostgreSQL 16 (local ou via Docker).

```bash
# Base de données (avec Docker)
docker compose -f infra/docker-compose.yml up -d

# API
cd services/api
cp ../../.env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload        # http://localhost:8000/docs

# Frontend
cd apps/web
npm install
npm run dev                                 # http://localhost:3000
```

## Tests et contrôles

```bash
cd services/api
uv run ruff check . && uv run ruff format --check . && uv run mypy app tests
uv run pytest                     # tests sans base
TEST_DATABASE=1 uv run pytest     # + migrations et santé sur PostgreSQL réel

cd apps/web
npm run lint && npm run typecheck && npm run build
npm run test:e2e   # Playwright : 9 pages × (ordinateur, mobile 360 px)
```

Les tests de bout en bout vérifient, pour chaque page et sur les deux formats : le rendu,
l'absence de violation d'accessibilité WCAG 2.1 A/AA (axe-core), l'absence de défilement
horizontal, l'absence d'erreur dans la console (dont les erreurs d'hydratation). Ils vérifient
aussi l'état des modules (API disponible ou injoignable), la persistance des préférences, le
chargement de la police tifinagh et le lien d'évitement au clavier.
Sans navigateur téléchargé par Playwright, indiquer un Chromium existant :
`PW_CHROMIUM_PATH=/chemin/vers/chrome npm run test:e2e`.

Les avertissements sont traités comme des erreurs dans pytest (fuites de connexions comprises).
