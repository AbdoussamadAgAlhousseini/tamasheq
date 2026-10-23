# Limites connues

Mis à jour le 2026-10-23.

## Langue

- **Aucune capacité en tamasheq n'a été évaluée.** L'assistant est expérimental ; ses réponses
  en tamasheq peuvent contenir des erreurs, des mots inexistants ou des formes d'autres langues
  amazighes.
- Il n'existe à notre connaissance aucun corpus tamasheq librement réutilisable pour
  l'entraînement (voir [research-and-sources.md](research-and-sources.md)).
- Aucune convention orthographique n'est encore fixée dans le projet (décision D4 en attente
  de formalisation).
- L'interface n'est disponible qu'en français et en anglais.

## Technique

- L'assistant dépend d'un fournisseur externe (Anthropic) : coût à l'usage, disponibilité et
  conditions du fournisseur.
- Les conversations ne sont pas conservées : recharger la page les efface.
- Limitation de débit en mémoire, valable pour une seule instance.
- Pas de connexion depuis l'interface web : contributions et relecture passent par l'API avec
  un jeton, ou par la ligne de commande.
- Le dictionnaire ne contient encore aucune donnée ; prononciation et audio arrivent en phase 6.
- Les conventions orthographiques sont enregistrables mais aucune conversion latin ↔ tifinagh
  n'est faite (volontairement : elle doit être définie et validée par des locuteurs).
- Traduction : modèle généraliste guidé par le dictionnaire, **non évalué** ; tamasheq produit
  en écriture latine seulement ; pas encore de comparaison avec NLLB-200.
- Recherche documentaire lexicale : un mot écrit autrement que dans le document (variante
  orthographique, synonyme) n'est pas retrouvé ; pas de liste de mots-outils tamasheq.
- La bibliothèque ne contient encore aucun document.
- Corrections de traductions : par l'API avec un jeton, pas encore depuis le site.
- Voix : collecte d'enregistrements seulement ; **aucune reconnaissance ni synthèse vocale**
  (modèles non téléchargeables dans l'environnement de développement, aucun évalué).
- Enregistrement testé avec Chromium ; Firefox et Safari produisent d'autres formats (Ogg,
  MP4), acceptés mais pas encore testés.
- Stockage audio local : un stockage objet (S3) sera nécessaire pour plusieurs serveurs.
