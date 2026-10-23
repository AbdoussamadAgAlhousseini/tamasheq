# Sécurité

État au 2026-10-23 (phase 3). À compléter à chaque phase ; audit complet prévu en phase 8.

## Secrets

- La clé `ANTHROPIC_API_KEY` reste **côté serveur** : lue par l'API depuis l'environnement,
  jamais envoyée au navigateur, jamais écrite dans les journaux (type `SecretStr`).
- Seule `NEXT_PUBLIC_API_URL` est exposée au navigateur ; elle ne contient pas de secret.
- Aucun fichier `.env` n'est versionné (`.gitignore`).
- Recommandé : fixer une **limite de dépenses** dans la console Anthropic.

## Assistant

- **Aucune conversation stockée** par TAMASHEQ : l'historique vit dans le navigateur et est
  renvoyé à chaque message. Les journaux ne contiennent que l'identifiant de requête, le
  modèle, la raison d'arrêt et les volumes de jetons, jamais le texte.
- **Limites** : 20 messages par conversation, 4 000 caractères par message, 10 requêtes par
  minute et par adresse IP (`CHAT_REQUESTS_PER_MINUTE`). Le limiteur est en mémoire : valable
  pour une seule instance de l'API. Derrière un proxy, l'adresse vue est celle du proxy ; à
  configurer au déploiement.
- **Injection de consignes** : le modèle n'a accès à aucun outil, aucune base de données et
  aucun document restreint ; un utilisateur ne peut donc rien obtenir d'autre que du texte
  généré. Les rôles autorisés sont `user` et `assistant` uniquement (pas de `system` côté
  client). Ce point devra être réexaminé avant la recherche documentaire (phase 5).
- Les messages sont transmis au fournisseur du modèle (Anthropic) ; l'interface demande de ne
  pas y écrire d'informations personnelles ni de savoirs restreints.

## API

- CORS limité aux origines de `CORS_ORIGINS`, en-tête `Content-Type` uniquement.
- Validation de toutes les entrées par Pydantic.
- Pas encore d'authentification : aucune route d'écriture de données n'existe.
