# Reels Library

Une bibliothèque personnelle pour retrouver et utiliser ses sauvegardes Instagram : idées de cuisine, veille et projets DIY. Première version en développement, destinée à un VPS ou à un conteneur, consultable sur ordinateur et téléphone.

## Fonctionnalités disponibles

- Ajout par lien Instagram et détection des doublons après normalisation.
- Import JSON ou texte avec aperçu, bilan par entrée et historique.
- Recherche avec ou sans accents dans les titres, notes, textes, thèmes, étiquettes et collections.
- Plusieurs thèmes par référence ; création, renommage et archivage des thèmes.
- Fiche modifiable, notes, intention, suivi personnel et sélection favorite.
- Conservation distincte des sources importées et corrections manuelles.
- Export réimportable des fiches et suppression des références.
- Connecteur expérimental de synchronisation des sauvegardes, tâches en arrière-plan et historique des erreurs.
- Image Docker, volumes persistants, accès privé et configuration HTTPS avec Caddy.

L'import de fichiers est testé sur des exemples synthétiques. **L'accès effectif aux sauvegardes depuis un VPS reste à valider avec une session Instagram réelle.** Aucun compte n'a été connecté pendant le développement. Le connecteur ne télécharge pas les vidéos et ne produit pas encore d'analyse IA.

## Démarrage avec Docker

Depuis le dépôt, avec Docker Compose et Python 3 disponibles :

```sh
python3 scripts/init_secrets.py
docker compose up -d --build
```

Sur Windows, utiliser `python` à la place de `python3`.

Ouvrir `http://localhost:8765`. Le navigateur demande l'identifiant **admin** et la clé contenue dans `secrets/app_token`. Le script conserve toute clé déjà présente et ne l'affiche pas dans les journaux.

Ce mode publie le port uniquement sur la boucle locale de l'hôte Docker. Sur un VPS, utiliser un tunnel SSH ou activer le déploiement HTTPS décrit dans le [guide VPS](docs/deploiement.md).

Les données et la session sont conservées dans deux volumes distincts. Une recréation du conteneur conserve ces volumes. `docker compose down` arrête le service ; l'option `--volumes` supprime les données persistantes.

## Connexion Instagram

Le serveur lit un fichier de session Instagram. La connexion initiale et ses renouvellements restent des opérations manuelles. Une fois la session transférée, les synchronisations s'exécutent sur le serveur : aucun ordinateur personnel ni navigateur ouvert n'est nécessaire.

1. Se connecter à Instagram dans un navigateur.
2. Préparer un fichier Netscape `cookies.txt`, ou utiliser l'[outil de préparation de session](docs/deploiement.md#préparer-la-session-instagram).
3. Transférer ce fichier depuis la page **Synchronisation** de l'application.
4. Tester un passage de 50 publications avant d'activer les passages réguliers.

La session donne accès au compte. Elle est filtrée pour ne conserver que les cookies Instagram, stockée dans un fichier distinct et exclue de l'export de bibliothèque. Les sorties brutes du connecteur ne sont ni affichées ni journalisées.

Instagram peut expirer la session, demander une vérification ou limiter l'accès depuis l'adresse IP du VPS. Ces cas arrêtent le passage et apparaissent dans l'historique. Une limite de lecture atteinte est signalée : la reprise complète d'un historique volumineux reste à développer.

## Développement sans Docker

Python 3.11 ou supérieur :

```sh
python -m venv .venv
```

Sous Windows :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-sync.txt
.\.venv\Scripts\python.exe -m reels_library
```

Sous Linux :

```sh
.venv/bin/python -m pip install -r requirements.txt -r requirements-sync.txt
.venv/bin/python -m reels_library
```

Ouvrir `http://127.0.0.1:8765`. `lancer.cmd` facilite ce lancement sur Windows. L'exécution sans clé est autorisée uniquement pour le développement sur la boucle locale. Le conteneur exige une clé.

## Import et exemples

Formats acceptés : fichier texte avec un lien par ligne ; liste JSON d'objets ; objets JSON contenant une liste `saved_saved_media`, `saved_media`, `saved_posts` ou `items` ; export produit par cette application.

Les liens des champs `string_map_data` et `string_list_data`, leurs dates de sauvegarde et les collections explicitement présentes sont pris en charge. Les archives ZIP, les exports HTML et les structures non reconnues sont refusés avec un motif. Le contenu exact d'un export réel reste à examiner.

Le fichier [instagram-demo.json](examples/instagram-demo.json) contient uniquement des exemples fictifs : six entrées donnent trois ajouts, un doublon, une entrée ignorée et une erreur. Les liens de démonstration ne désignent pas de véritables vidéos.

## Vérification

```sh
python -m unittest discover -v
docker build -t reels-library:dev .
python scripts/smoke_container.py
```

Le test Docker utilise des données et une session fictives, vérifie l'accès privé et la persistance après recréation, puis supprime uniquement ses propres conteneurs et volumes éphémères. Il n'appelle pas Instagram.

## Documentation

- [Cadrage initial](docs/cadrage.md)
- [Décisions actualisées](docs/decisions.md)
- [Déploiement sur VPS](docs/deploiement.md)
- [Architecture et limites](docs/architecture.md)
- [Prochaines étapes](docs/prochaines-etapes.md)
