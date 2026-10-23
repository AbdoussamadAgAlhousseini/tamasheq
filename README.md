# TAMASHEQ

Infrastructure linguistique et d'intelligence artificielle pour la langue tamasheq du Mali
(`taq`) et les savoirs touaregs, gouvernée avec les communautés. Projet non commercial.

> **Statut : phase 6 terminée (collecte vocale).**
> - Expérimental et **non évalué** : assistant, traduction, réponses citées (actifs seulement
>   si une clé `ANTHROPIC_API_KEY` est fournie).
> - Fonctionnels : dictionnaire, corpus, bibliothèque des savoirs (provenance, droits,
>   niveaux d'accès, validation, retrait) et collecte d'enregistrements consentie.
> - Absents : reconnaissance et synthèse vocales (aucun modèle évalué).
> - **Aucune donnée tamasheq, aucun document ni aucun enregistrement n'est encore chargé.**

## Démarrage rapide

```bash
docker compose -f infra/docker-compose.yml up -d     # PostgreSQL 16 (FFmpeg requis pour l'audio)
cd services/api && cp ../../.env.example .env && uv sync && uv run alembic upgrade head
uv run uvicorn app.main:app --reload                 # http://localhost:8000/docs
cd ../../apps/web && npm install && npm run dev      # http://localhost:3000
```

Détails, tests et contrôles : [docs/architecture.md](docs/architecture.md).

## Documents

- [Rapport de phase 0](docs/phase-0-report.md) : état des lieux, jeux de données, modèles candidats, risques, plan.
- [Recherche et sources](docs/research-and-sources.md) : sources, niveau de vérification, licences.
- [Registre des décisions](docs/decisions.md)
- [Architecture](docs/architecture.md) · [Déploiement](docs/deployment.md)
- [Gouvernance des données](docs/data-governance.md) · [Constitution des corpus](docs/data-collection.md)
- [Évaluation](docs/evaluation.md) · [Sécurité](docs/security.md) · [Limites connues](docs/limitations.md)

## Principes

1. Aucune donnée tamasheq inventée ; aucune source inventée.
2. Une licence publique n'est pas une autorisation d'entraînement.
3. Tamasheq ≠ tamazight.
4. Aucune performance annoncée sans méthodologie et résultats reproductibles.
5. Gouvernance des données selon les principes CARE.

## Licence

Code sous licence [GNU AGPL-3.0](LICENSE) (décision D10). Les données et modèles tiers
gardent leurs propres licences ; les contributions linguistiques ont leur propre régime de
droits, défini contribution par contribution.
