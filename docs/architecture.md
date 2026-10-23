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
```

Les avertissements sont traités comme des erreurs dans pytest (fuites de connexions comprises).
