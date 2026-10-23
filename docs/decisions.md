# Décisions et questions ouvertes

Mise à jour : 23 octobre 2026.

## Confirmé par l'utilisateur

| Sujet | Décision |
| --- | --- |
| Public initial | Usage personnel ; ouverture possible ensuite |
| Premier usage | Bibliothèque : importer, classer et retrouver |
| Appareils | Ordinateur et téléphone |
| Synchronisation | Automatique, indispensable au produit |
| Hébergement | VPS ou conteneur ; l'ordinateur personnel ne doit pas être nécessaire au fonctionnement |
| Source | Reels Instagram sauvegardés |
| Organisation | Catégories évolutives, domaines ouverts |
| Parcours | Sans Hermes ni iMessage |
| Compte Instagram | Aucune connexion dans un navigateur au moment des échanges |

## Choix de ce premier incrément

- Application web responsive, serveur Python WSGI/Waitress, base SQLite relationnelle.
- Déploiement Docker Compose, un seul processus applicatif et un planificateur interne.
- Volumes séparés pour bibliothèque et session Instagram ; clé d'accès injectée par secret Compose.
- Accès distant personnel par authentification HTTP Basic (`admin` et clé longue) derrière HTTPS.
- Synchronisation expérimentale via `gallery-dl`, à partir d'un fichier de session conservé côté serveur. Le service ne lit pas le navigateur du poste personnel pendant ses passages.
- Connexion initiale et renouvellement de session manuels. L'outil d'export de navigateur est facultatif et sert uniquement à préparer la connexion.
- Bibliothèque commune et classement manuel avant les modules spécialisés et l'analyse IA.
- Réimport sans écrasement des corrections personnelles ; nouvelles sources conservées séparément.

Ces choix constituent une base de prototype. La validation de l'accès à Instagram depuis le VPS précède la promesse d'une synchronisation fiable.

## Questions encore ouvertes

- Volume historique et nombre de nouvelles sauvegardes par semaine.
- VPS, domaine et reverse proxy déjà disponibles ou à choisir.
- Acceptabilité du renouvellement manuel d'une session expirée.
- Budget et mode de traitement pour la future analyse.
- Premier module spécialisé et outils existants à intégrer.

## Validation restante

L'extracteur est installé, les contrats de données et la gestion des erreurs sont testés avec des réponses simulées. Aucun compte réel n'a été utilisé. La connexion initiale, les challenges éventuels, la stabilité de l'accès depuis un VPS et la couverture des contenus privés/supprimés restent à mesurer.
