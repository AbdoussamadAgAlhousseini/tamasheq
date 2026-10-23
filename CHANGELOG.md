# Changelog

## [Non publié]

### Ajouté
- Phase 5 : traduction expérimentale (`POST /api/v1/translate`) appuyée sur les entrées
  validées du dictionnaire, avec ambiguïtés, variantes et entrées utilisées ; corrections par
  les locuteurs versées au corpus. Bibliothèque des savoirs (migration `0003`) : documents à
  trois niveaux d'accès, passages indexés, recherche plein texte, réponses citées fondées sur
  les seuls documents publics (`POST /api/v1/knowledge/ask`). Couche d'accès au modèle
  partagée, routes de cycle de vie communes, import `knowledge` en ligne de commande. Outils
  d'évaluation : chrF++ et notation humaine (traduction), rappel@k et MRR (recherche).
  Pages `/translate` et `/knowledge` fonctionnelles.
- Phase 4 : dictionnaire et corpus. Migration `0002` (sources, entrées, graphies, sens,
  exemples, textes, conventions, révisions, exports, jetons), garanties en base (forme
  d'origine immuable, journal append-only), jetons d'accès et rôles, contrôle à quatre yeux,
  API du dictionnaire, outil `app.cli` (comptes, sources, import tout-ou-rien, exports
  traçables, retraits), page `/dictionary` avec recherche et préférence d'écriture. Documents
  `data-governance.md` et `data-collection.md`.
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
