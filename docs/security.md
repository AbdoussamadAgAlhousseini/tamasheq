# Sécurité

État au 2026-10-23 (phase 5). À compléter à chaque phase ; audit complet prévu en phase 8.

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

## Traduction et réponses citées

- Seuls les contenus **publics** sortent vers le fournisseur du modèle : entrées du
  dictionnaire validées et publiables (glossaire), passages de documents validés, publiables
  et de niveau public. Les documents « membres » et restreints ne lui sont jamais transmis.
- Injection de consignes : le texte à traduire, la question et les passages sont encadrés et
  échappés (`<`, `>`, `&`), et les consignes demandent de les traiter comme des données. Le
  modèle n'a aucun outil ; les citations sont limitées par schéma aux passages fournis, puis
  revérifiées côté serveur.
- La session de base de données est fermée avant l'appel au modèle.

## Authentification

- Jetons porteurs aléatoires (256 bits), créés en ligne de commande, montrés une seule fois ;
  seule leur empreinte SHA-256 est stockée. Révocation : `app.cli revoke-tokens`.
- Pas de mot de passe stocké. Une connexion depuis l'interface web reste à concevoir.
- Rôles vérifiés à chaque requête ; contrôle à quatre yeux pour la validation.

## API

- CORS limité aux origines de `CORS_ORIGINS`, en-têtes `Content-Type` et `Authorization`.
- Validation stricte des entrées par Pydantic (champs inconnus refusés, tailles bornées).
- Recherche : caractères spéciaux de `LIKE` neutralisés ; requêtes SQL paramétrées.
- Vue publique du dictionnaire : aucune donnée sur le contributeur ni sur le consentement.
