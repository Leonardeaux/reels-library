# Reels Library

Une bibliothèque personnelle pour importer, classer et retrouver ses sauvegardes Instagram. Chaque personne installe sa propre application, conserve sa bibliothèque et utilise sa propre session Instagram.

**Installation recommandée : un conteneur Docker sur ton ordinateur, puis une interface dans ton navigateur.** Tu peux aussi l'installer sur un NAS ou un serveur. Aucun VPS, domaine, compte Reels Library ou service central n'est nécessaire. Il ne s'agit pas d'un exécutable desktop natif.

Le code du projet est sous [licence MIT](LICENSE). Les dépendances conservent leurs [licences respectives](THIRD_PARTY_NOTICES.md).

**État : prototype fonctionnel.** Bibliothèque, imports, recherche, authentification et persistance du conteneur sont testés. La synchronisation Instagram est expérimentale et reste à valider sur compte réel. Il n'y a pas encore d'analyse IA, de transcription ni de classement automatique.

## Installer chez soi

### 1. Récupérer le projet

Télécharge le code depuis **Code → Download ZIP** sur GitHub et extrais l'archive, ou utilise Git :

```sh
git clone https://github.com/Leonardeaux/reels-library.git
cd reels-library
```

Ouvre un terminal dans le dossier contenant `compose.yaml`.

Le seul prérequis pour lancer l'application est **Docker avec Compose**. Sur Windows et macOS, démarre Docker Desktop ; sur Windows, utilise les conteneurs Linux. Sur Linux, utilise Docker Engine avec le plugin Compose. Python et Git ne sont pas nécessaires pour le parcours ZIP + Docker.

### 2. Démarrer

```sh
docker compose up -d --build
docker compose ps
```

Le premier lancement télécharge et construit l'image. Attends que `app` soit `healthy`, puis ouvre **http://localhost:8765**.

Une clé privée est créée automatiquement au premier démarrage, sans être écrite dans les journaux. Pour l'afficher volontairement dans ton terminal :

```sh
docker compose exec app python -m reels_library.access_key
```

Connecte-toi avec l'identifiant **`admin`** et cette clé comme mot de passe. Cette clé protège ta bibliothèque ; elle est distincte du cookie Instagram. Chaque installation possède sa propre clé, conservée après redémarrage.

Tu n'as besoin ni de `.env` ni de `scripts/init_secrets.py` pour ce démarrage. Pour changer le port, copie `.env.example` vers `.env` et modifie `REELS_PORT`, puis relance Compose. Par exemple, `REELS_PORT=8766` donne `http://localhost:8766`.

Le port est publié uniquement sur cet ordinateur. Pour accéder à une installation sur un autre appareil, consulte l'[option d'accès distant](docs/deploiement.md).

### 3. Essayer sans compte Instagram

Dans **Importer**, choisis [`examples/instagram-demo.json`](examples/instagram-demo.json), puis vérifie l'aperçu : **3 ajouts, 1 doublon, 1 entrée ignorée et 1 erreur** sur une bibliothèque vide. L'erreur fait volontairement partie de la démonstration. Confirme ensuite l'import.

Tu peux modifier les fiches, ajouter des notes, classer par thème, utiliser les filtres et exporter ta bibliothèque. Les liens de démonstration sont fictifs. Le [parcours de test détaillé](docs/test-manuel.md) donne les résultats attendus et explique le réimport.

### 4. Relier tes sauvegardes Instagram

Dans **Synchronisation**, importe un fichier de cookies Instagram au format Netscape contenant une session `sessionid` valide. Si tu possèdes déjà ce fichier, aucun Python n'est nécessaire sur l'hôte. Le [guide de connexion](docs/connexion-instagram.md) explique aussi l'outil facultatif d'export de navigateur et les erreurs de lecture Chrome, Edge ou Firefox.

Lance d'abord **Tester et synchroniser** avec 50 publications. Active les passages réguliers après un essai réussi. Le format et l'expiration du fichier sont vérifiés à l'import ; seul un passage réel permet de confirmer qu'Instagram accepte la session.

Le backend dans le conteneur contacte Instagram, puis enregistre les informations en local. L'interface ne reçoit pas les valeurs des cookies. **La synchronisation continue quand tu fermes l'onglet, tant que le conteneur et son ordinateur fonctionnent.** Elle s'arrête si tu arrêtes Docker ou éteins cet ordinateur, puis reprend au démarrage si elle est activée.

Le cookie donne accès au compte : garde-le confidentiel et ne le publie pas sur GitHub. Instagram peut l'invalider avant son expiration déclarée ; la version actuelle ne le renouvelle pas automatiquement. Il faut alors importer une nouvelle session.

## Fonctions disponibles

| Fonction | Comportement |
| --- | --- |
| Ajout par lien | Références Instagram `/reel/`, `/reels/` ou `/p/`, avec détection des doublons |
| Import | JSON ou TXT, aperçu avant enregistrement, bilan et historique |
| Organisation | Thèmes, étiquettes, collections personnelles, notes et sélection par étoile |
| Recherche | Texte avec ou sans accents et filtres par classement ou suivi |
| Suivi | À utiliser, En cours, Utilisé, Archivé |
| Provenance | Sources importées séparées des corrections personnelles |
| Export | JSON réimportable des fiches, de leur classement et de leurs sources |
| Synchronisation | Lecture expérimentale des sauvegardes, manuelle ou périodique |

Un lien seul ne fournit pas le contenu de la vidéo. Une légende disponible ne garantit pas une transcription complète. Aucun média n'est téléchargé par la synchronisation actuelle.

**Supprimer une référence agit uniquement dans cette bibliothèque.** Cela ne supprime pas de publication et ne retire rien des enregistrements Instagram. Le connecteur ne supprime pas non plus les fiches locales retirées d'Instagram.

## Données et mises à jour

Les données personnelles sont séparées du code téléchargé :

| Volume Docker | Contenu |
| --- | --- |
| `library_data` | Base SQLite : fiches, notes, classement, réglages et historiques |
| `instagram_session` | Fichier de session Instagram, hors base et hors export |
| `app_config` | Clé privée de l'installation |

Les volumes portent par défaut le préfixe `reels-library_`. Le nom de projet est fixé dans Compose pour que remplacer ou renommer le dossier du code ne change pas la bibliothèque utilisée. Deux copies du dépôt sur le même Docker utilisent donc la même installation par défaut. Pour une seconde installation indépendante, définis un autre `COMPOSE_PROJECT_NAME` et un autre `REELS_PORT` dans son `.env`.

Pour arrêter ou reprendre :

```sh
docker compose stop
docker compose start
```

Avec Git, pour mettre à jour :

```sh
git pull --ff-only
docker compose up -d --build
```

Avec une archive ZIP, remplace le code par la nouvelle version, reporte ton `.env` éventuel, puis relance `docker compose up -d --build`. Les volumes sont conservés. **N'utilise pas `docker compose down -v` pour une mise à jour : cette option supprime les volumes et les données.**

Utilise **Exporter ma bibliothèque** pour un fichier JSON portable. Il contient les fiches et leurs sources, mais pas le cookie, la clé, les réglages de synchronisation ni l'historique des traitements. Pour une sauvegarde complète, arrête le conteneur et sauvegarde les trois volumes ; protège la session et la clé séparément.

### Si tu utilisais la version précédente

Les volumes `library_data` et `instagram_session` sont conservés avec le même nom de projet Compose. Ils ne sont pas importés depuis les dossiers utilisés par un lancement Python direct.

La clé est désormais créée dans `app_config` : récupère-la avec la commande de connexion ci-dessus. L'ancien fichier `secrets/app_token` n'est plus nécessaire au Compose par défaut et n'est pas supprimé. Si le nom de ton ancien projet Compose était différent de `reels-library`, garde ce nom avec `COMPOSE_PROJECT_NAME` pour retrouver ses volumes.

## Dépannage

| Problème | Action |
| --- | --- |
| Docker ne répond pas | Démarre Docker Desktop ou le service Docker ; vérifie `docker compose version` |
| Port 8765 déjà pris | Définis `REELS_PORT=8766` dans `.env`, puis relance Compose |
| Connexion refusée dans le navigateur | Attends le statut `healthy` ; vérifie `docker compose logs --tail=100 app` |
| Mot de passe refusé | Relis la clé avec `docker compose exec app python -m reels_library.access_key` |
| Mauvais hôte ou origine refusée | Ouvre l'adresse configurée ; pour une installation locale, retire l'ancien `REELS_PUBLIC_URL` distant du `.env` |
| Lecture des cookies impossible | Consulte le [diagnostic des navigateurs](docs/connexion-instagram.md#si-chrome-sous-windows-ne-permet-pas-la-lecture) |
| Synchronisation refusée | Renouvelle la session, vérifie les demandes de connexion sur Instagram et réessaie plus tard en cas de limitation |
| Bibliothèque vide après déplacement | Vérifie le contexte Docker et le nom du projet Compose : les volumes ne sont pas transférés entre ordinateurs |

## Structure et contributions

```text
reels_library/       Backend Python, SQLite, connecteur et interface static/
tests/              Tests automatisés avec données fictives
examples/           Fichier de démonstration
scripts/            Vérification Docker et outils facultatifs
docs/               Connexion, tests, architecture et développement
deploy/             Reverse proxy HTTPS facultatif
compose.yaml        Installation locale par défaut
Dockerfile          Image de l'application
.github/workflows/  Vérifications Python et Docker sur GitHub
```

Le [guide de développement](docs/developpement.md) explique le lancement Python et les tests. Lis aussi les [règles de contribution](CONTRIBUTING.md), l'[architecture](docs/architecture.md), les [décisions](docs/decisions.md) et les [prochaines étapes](docs/prochaines-etapes.md).

La récupération Instagram complète, la pagination historique et la stabilité d'une session sur la durée restent à valider. La fenêtre actuelle est limitée à 50, 200, 1 000 ou 5 000 publications par passage. Le code est disponible sous MIT ; ce projet n'est pas un produit officiel Instagram ou Meta.
