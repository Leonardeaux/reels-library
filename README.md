# Reels Library

Nom provisoire du projet.

Transformer ses Reels Instagram sauvegardés en ressources faciles à retrouver et à utiliser : recettes, fiches de veille informatique et projets DIY ou impression 3D.

## État du projet

Phase de cadrage. Le dépôt contient la documentation initiale ; aucune fonctionnalité applicative n'est encore implémentée.

- Usage personnel au départ, ouverture possible à d'autres utilisateurs.
- Catégories évolutives et plusieurs catégories possibles par Reel.
- Parcours souhaité sans Hermes ni iMessage.
- Méthode de récupération, premier module et technologies à valider.

## Documentation

- [Cadrage du projet](docs/cadrage.md)
- [Décisions et questions ouvertes](docs/decisions.md)
- [Prochaines étapes](docs/prochaines-etapes.md)

## Organisation envisagée

Récupération des références → acquisition du contenu accessible → analyse → bibliothèque → modules spécialisés.

Les sources brutes et les résultats d'analyse seront séparés. Les informations manquantes resteront explicites.

## Référence étudiée

[reels-vault, par sosoj92](https://github.com/sosoj92/reels-vault) fournit une piste à évaluer pour l'ingestion et la transcription.

Aucun code de ce dépôt tiers n'a été repris dans cette initialisation. Son fonctionnement sur le compte de l'utilisateur reste à tester.

## Données personnelles

Les exports Instagram, cookies, secrets, médias et modèles locaux ne doivent pas être ajoutés au dépôt. Des exclusions sont prévues dans le fichier .gitignore.

Le dépôt ne contient aucune donnée Instagram ni aucun accès à un compte.
