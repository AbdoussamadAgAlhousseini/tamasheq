# Déploiement

> Statut : **recommandation** (décision D7 déléguée). Rien n'est déployé. Les tarifs et
> régions des fournisseurs n'ont pas pu être vérifiés pendant la phase 0 (accès réseau
> restreint) et doivent l'être avant la création des comptes.

## Contraintes retenues

- Utilisateurs principalement au Mali, souvent sur mobile et avec des connexions lentes.
- Projet non commercial et à budget limité, porté au départ par une seule personne : il faut
  le moins d'administration système possible.
- Données communautaires : hébergement dans une juridiction offrant un cadre de protection
  des données solide, sauvegardes et restauration testées.
- Aucun verrouillage : conteneurs standards et PostgreSQL standard, migrables ailleurs.

## Recommandation

| Composant | Choix recommandé | Raison |
|---|---|---|
| Frontend | **Vercel** | Hébergeur natif de Next.js, déjà utilisé par le porteur du projet, CDN mondial pour des pages légères. |
| API | Service de conteneurs managé, **région Europe** (ex. Render, Fly.io, Scaleway) | Pas de serveur à administrer. L'Europe offre une latence plus faible depuis le Mali que l'Amérique du Nord, et le RGPD comme cadre de protection. |
| PostgreSQL | PostgreSQL managé en Europe avec sauvegardes automatiques (ex. Neon, ou l'offre du même hébergeur que l'API) | Sauvegardes et restauration à un instant donné sans administration. |
| Audio | Répertoire persistant (`AUDIO_STORAGE_DIR`) sur un seul serveur ; stockage objet compatible S3 en Europe dès qu'il y a plusieurs instances | L'API doit disposer de FFmpeg (`ffprobe`). Sauvegarder ce répertoire avec la base. |
| Calcul ML (phases 6–7) | GPU loué à la demande | Inutile tant qu'aucun modèle local n'est entraîné. |

Alternative plus économique mais plus exigeante : un serveur unique (VPS européen) avec
docker compose, au prix d'une administration et de sauvegardes à gérer soi-même.

## Environnements

| Environnement | Contenu |
|---|---|
| Local | Voir [architecture.md](architecture.md#lancement-local). |
| Test (préproduction) | À définir en phase 8 : mêmes services, base séparée, données factices uniquement. |
| Production | À définir en phase 8, après audit de sécurité et test de restauration. |
