# Changelog

## [Non publié]

### Ajouté
- Phase 3 : assistant expérimental. `POST /api/v1/chat`, interface `ChatProvider` et adaptateur
  Anthropic (`claude-opus-5-5`, repli serveur), consignes de prudence, limites de taille et de
  débit, page `/chat` interactive quand l'assistant est configuré, réponses marquées « non
  vérifiées ». Outil d'évaluation (`app.evaluation.chat_eval`) et protocole de notation par
  des locuteurs (`evaluation/chat/`). Documents `evaluation.md`, `security.md`,
  `limitations.md`.
- Phase 2 : 9 pages (`/`, `/chat`, `/translate`, `/dictionary`, `/knowledge`, `/voice`,
  `/contribute`, `/admin`, `/about`), navigation responsive, sélecteurs de langue (FR/EN) et
  d'écriture (latin/tifinagh), état des modules lu depuis l'API, police Noto Sans Tifinagh
  auto-hébergée, tests Playwright (accessibilité axe WCAG 2.1 AA, mobile 360 px, console).
- Licence du code GNU AGPL-3.0 (`LICENSE`, décision D10).
- Phase 1 : frontend Next.js 16 (`apps/web`), API FastAPI (`services/api`) avec `/health` et
  `/api/v1/capabilities`, migration Alembic `0001` (utilisateurs et rôles), PostgreSQL de
  développement (`infra/`), CI GitHub Actions, `.env.example`.
- Documentation : `docs/decisions.md`, `docs/architecture.md`, `docs/deployment.md`.
- Phase 0 : `docs/research-and-sources.md` et `docs/phase-0-report.md` (2026-10-23).

### Modifié
- Projet renommé de « AKAL Tamasheq » en **TAMASHEQ** (décision D1).
