# Prochaines étapes

## Réalisé dans la première base

Bibliothèque, ajout par lien, imports avec bilan, recherche et filtres, thèmes, collections, notes, suivi, export et suppression. Connecteur de synchronisation en arrière-plan, stockage de session côté serveur, conteneur Docker et accès distant privé préparés.

## 1. Valider l'accès depuis le VPS

Déployer la base, établir une session Instagram et tester 30 à 50 sauvegardes. Mesurer les références accessibles, légendes, dates effectivement disponibles, erreurs, contenus privés ou supprimés et temps de traitement. Confirmer que l'accès continue lorsque l'ordinateur personnel est éteint.

Cette étape est bloquante pour valider la synchronisation réelle, mais pas pour utiliser et tester la bibliothèque avec des liens ou fichiers.

## 2. Fiabiliser la synchronisation

Tester expiration de session, interruptions et limitations côté Instagram. Ajouter pagination et point de reprise persistants pour l'historique complet. La version actuelle relit une fenêtre de 50, 200, 1 000 ou 5 000 publications, signale la limite et déduplique les résultats. Elle ne supprime pas une référence retirée des sauvegardes Instagram.

## 3. Essayer les parcours sur ordinateur et téléphone

Vérifier visuellement recherche, import, modification et synchronisation sur les appareils réels. Aucun navigateur pilotable n'était disponible pour la vérification visuelle pendant ce développement.

## 4. Ajouter l'analyse lorsque les sources sont accessibles

Conserver légendes, transcriptions et éventuelles images avec leur provenance. Mesurer qualité et coût avant activation de traitements massifs. Ne pas déduire de contenu à partir d'un lien seul.

## 5. Choisir le premier module spécialisé

Recettes, veille ou projets DIY, selon les retours sur la bibliothèque. Définir les informations indispensables et les champs qui doivent rester inconnus quand la source est incomplète.
