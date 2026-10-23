# Gouvernance des données

Cadre : principes CARE (Carroll et al., *Data Science Journal*, 2020) — bénéfice collectif,
autorité de contrôle, responsabilité, éthique. Décisions de référence : D4 et D5 dans
[decisions.md](decisions.md) (conventions et gouvernance décidées par le porteur du projet, en
attendant une instance communautaire).

## Rôles

| Rôle | Peut |
|---|---|
| `contributor` | Proposer des entrées ; retirer **ses** contributions |
| `reviewer` | Valider ou restreindre les contributions **des autres** ; consulter l'historique |
| `admin` | Tout ce qui précède ; retirer n'importe quel contenu ; créer les comptes ; exporter |

Les comptes et jetons sont créés par l'administration (`python -m app.cli create-user`).

## Cycle de vie d'un contenu

```
          import                    contribution
            │                            │
            ▼                            ▼
          brut ──── validation ──▶ ◀── en attente
            │          │                 │
            │          ▼                 │
            │       validé               │
            │          │                 │
            └──────────┼─────────────────┘
                       ▼
         restreint (motif obligatoire)        retiré (à tout moment, motif obligatoire)
```

| Statut | Visible publiquement | Exportable |
|---|---|---|
| `raw` (brut) | non | non |
| `pending` (en attente) | seulement si l'utilisateur le demande, marqué « non validée » | non |
| `validated` (validé) | oui, si la publication est autorisée | selon les autorisations |
| `restricted` (restreint) | non | non |
| `withdrawn` (retiré) | non | non |

## Règles appliquées par le code

1. **Deux autorisations distinctes**, explicites et sans valeur par défaut à la saisie :
   publication (`allow_publication`) et entraînement de modèles (`allow_training`).
2. **Contrôle à quatre yeux** : une contribution ne peut pas être validée par la personne qui
   l'a proposée.
3. **Exports d'entraînement** : il faut l'accord du contributeur **et** une source dont la
   licence autorise l'entraînement. Une licence au statut inconnu vaut « non ».
4. **Restrictions de diffusion** : tout contenu qui en porte est exclu des exports
   automatiques ; l'administration décide au cas par cas.
5. **Traçabilité des exports** : chaque export enregistre la liste exacte de ses éléments et
   l'empreinte SHA-256 du fichier produit.
6. **Retrait** : le contenu passe au statut retiré, disparaît de l'affichage et des exports
   futurs, et l'outil liste les exports déjà produits qui le contenaient. Un modèle déjà
   entraîné sur un export concerné ne peut pas « oublier » ce contenu : la politique à suivre
   (réentraînement, signalement) est à définir avec les communautés avant tout entraînement.

## Garanties en base de données

Indépendamment du code applicatif, PostgreSQL refuse :
- toute modification de la forme d'origine d'une entrée (`headword`) ou d'un texte
  (`original_text`) ;
- toute modification ou suppression du journal des révisions.

## Questions ouvertes

- Instance communautaire de gouvernance et procédure d'appel (D5).
- Niveaux d'accès communautaires pour les savoirs (phase 5).
- Durée de conservation des contenus retirés (aujourd'hui : conservés, marqués, pour la trace).
