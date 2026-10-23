# Évaluation

> Aucun résultat d'évaluation n'existe encore. Ce document fixe la méthode avant les mesures.

## Principes

1. **Les locuteurs jugent.** Les scores automatiques (chrF++, BLEU, WER, CER) complètent le
   jugement humain sans le remplacer.
2. **Jeux séparés.** Les données de test ne servent jamais à l'entraînement ni à l'ajustement
   des consignes ; elles ne sont pas montrées au modèle en dehors des passes d'évaluation.
3. **Tout est daté et versionné** : modèle réellement utilisé, consignes (`prompt_sha256`),
   date, jeu de questions, évaluateurs (pseudonymes).
4. **Les limites sont publiées** avec les résultats : taille du jeu, variantes couvertes,
   nombre d'évaluateurs, désaccords.
5. **Changer de modèle ou de consignes oblige à refaire une passe.**

## Statuts d'une capacité

| Statut | Condition |
|---|---|
| `not_available` | Fonction absente ou non configurée |
| `experimental` | Fonction active, **non évaluée** ; chaque réponse est marquée « non vérifiée » |
| `evaluated` | Résultats d'une passe publiés dans `evaluation/`, limites documentées |

Le statut `evaluated` ne dit pas que la fonction est bonne : il dit que sa qualité est connue
et publiée.

## Par module

| Module | Méthode | Où |
|---|---|---|
| Assistant | 50 questions de référence, ≥ 2 évaluateurs, barème sens/langue/orthographe/inventions/incertitude/refus | [evaluation/chat/](../evaluation/chat/README.md) |
| Traduction | Phase 5 : chrF++ sur jeu de test indépendant + jugement humain (fidélité, grammaire, naturel, omissions, ajouts) | à venir |
| Voix | Phase 6 : WER/CER avec normalisation documentée, locuteurs et conditions séparés ; TTS jugée par des locuteurs | à venir |
| Dictionnaire, tifinagh | Phase 4 : correspondances entre écritures, collisions, recherche normalisée | à venir |
