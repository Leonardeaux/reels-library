# Décisions

Mise à jour : 25 octobre 2026.

## Confirmé par l'utilisateur

| Sujet | Décision |
| --- | --- |
| Distribution | Projet open source disponible sur GitHub, installable par chacun |
| Licence du code du projet | MIT |
| Exécution | Serveur web dans un conteneur, interface dans un navigateur |
| Hébergement | Au choix de l'utilisateur ; aucun VPS imposé |
| Usage initial | Bibliothèque : importer, classer et retrouver |
| Source | Reels Instagram sauvegardés |
| Synchronisation | Automatique, indispensable au produit |
| Organisation | Catégories évolutives et domaines ouverts |
| Parcours | Sans Hermes ni iMessage |

La demande initiale d'un service fonctionnant obligatoirement sur VPS est remplacée par cette distribution à installer chez soi. Le terme desktop décrit ici l'usage depuis son ordinateur ; une fenêtre native et des installateurs par système ne font pas partie du choix retenu. L'accès depuis un téléphone reste possible avec une installation distante configurée volontairement.

## Choix techniques

- Un même cœur Python WSGI/Waitress, SQLite et frontal HTML/CSS/JavaScript.
- Docker Compose comme parcours utilisateur principal, sans Python obligatoire sur l'hôte.
- Création automatique d'une clé privée par installation, persistée dans un volume distinct.
- Volumes séparés pour bibliothèque, session Instagram et configuration ; code de l'image en lecture seule.
- Accès local par défaut sur la boucle locale, authentification conservée.
- HTTPS et reverse proxy facultatifs pour une installation distante.
- gallery-dl lancé séparément pour lire les sauvegardes avec une session fournie par l'utilisateur.
- Connexion initiale et renouvellement de la session manuels ; l'export de navigateur est facultatif.
- MIT pour le code du projet ; licences propres aux dépendances, dont GPL-2.0-only pour gallery-dl.
- Aucune bibliothèque, session, télémétrie ou inscription centralisée chez l'auteur du projet.

## À valider

- Accès Instagram sur un compte réel et stabilité dans la durée.
- Volume historique et couverture des légendes, contenus privés ou supprimés.
- Parcours Docker sur Windows, macOS et Linux avec utilisateurs réels.
- Pagination et reprise persistante de l'historique.
- Premier module spécialisé et éventuelle analyse du contenu.

Le dépôt et sa visibilité GitHub sont des sujets distincts de la licence. Rendre le dépôt public est nécessaire pour distribuer librement son code à tous ; l'ajout de MIT ne modifie pas automatiquement cette visibilité.
