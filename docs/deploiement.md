# Déploiement sur VPS

La cible est un service personnel permanent. Le VPS exécute l'interface, la base et les passages de synchronisation. Le téléphone et l'ordinateur servent de clients web.

## Accès par tunnel SSH

Prérequis : Docker avec Compose sur le VPS, Python 3 pour initialiser la clé, accès SSH au serveur.

Dans le dépôt sur le VPS :

```sh
python3 scripts/init_secrets.py
docker compose up -d --build
```

Sur l'ordinateur client :

```sh
ssh -L 8765:127.0.0.1:8765 utilisateur@adresse-du-vps
```

Ouvrir `http://localhost:8765`. Identifiant : `admin`. La clé est dans `secrets/app_token` sur le VPS. Le port publié par Compose est lié à `127.0.0.1` sur le VPS.

## Accès HTTPS sur ordinateur et téléphone

Faire pointer un domaine ou sous-domaine sur l'IP du VPS. Autoriser les ports 80 et 443 dans son pare-feu. Copier `.env.example` vers `.env`, puis renseigner :

```dotenv
REELS_DOMAIN=reels.exemple.fr
REELS_PUBLIC_URL=https://reels.exemple.fr
```

```sh
python3 scripts/init_secrets.py
docker compose --profile public up -d --build
```

Ouvrir l'adresse HTTPS depuis chaque appareil et utiliser `admin` avec la clé privée. Caddy termine HTTPS et transmet les requêtes à l'application ; le nom d'hôte et les origines acceptés sont limités à `REELS_PUBLIC_URL`.

Avec un reverse proxy existant, utiliser le service `app` seul et transmettre le domaine configuré dans l'en-tête `Host`. Le processus applicatif ne fait pas confiance aux en-têtes de proxy pour décider de l'origine autorisée.

La clé est montée comme secret dans `/run/secrets/app_token`. Le conteneur fonctionne avec l'UID 10001 et un système de fichiers applicatif en lecture seule. Les données modifiables sont dans des volumes. Le répertoire `secrets/` sur l'hôte est privé ; le script d'initialisation prépare les permissions de lecture nécessaires au montage du secret dans le conteneur non root.

## Préparer la session Instagram

Le connecteur utilise une session de compte, pas un jeton d'API Meta. La [configuration de gallery-dl](https://gdl-org.github.io/docs/configuration.html#extractor-cookies) prend en charge un fichier de cookies Netscape. La faisabilité de la lecture des sauvegardes depuis l'IP du VPS reste à vérifier.

Sur une machine où un navigateur est connecté à Instagram, installer les dépendances du projet, puis lancer volontairement :

```sh
python -m reels_library.export_session --browser firefox
```

Les valeurs acceptées sont `firefox`, `edge` et `chrome`. La commande prépare `sessions/instagram.cookies`, contenant uniquement la session Instagram. L'accès aux cookies dépend du navigateur et de ses protections ; un échec est signalé sans afficher les valeurs de session.

Sur Windows, les cookies Chrome protégés par App-Bound Encryption ne sont pas déchiffrables par le lecteur Windows du connecteur utilisé dans cette version. Le code `COOKIES_DECRYPTION_FAILED` signale un problème de déchiffrement. Pour préparer la session avec Firefox, connecte-toi à Instagram dans Firefox puis utilise `--browser firefox`. Le VPS reste autonome une fois le fichier transféré.

Pour un profil précis, ajoute par exemple `--profile "Profile 1"` ou le chemin de son dossier. L'option cible le profil connecté et ne modifie pas les protections de chiffrement. Les codes `COOKIES_LOCKED` et `COOKIES_PROFILE_NOT_FOUND` distinguent un accès au fichier bloqué d'un profil introuvable. Le [tableau de diagnostic du README](../README.md#si-chrome-sous-windows-ne-permet-pas-la-lecture) décrit les actions correspondantes.

Dans l'application hébergée en HTTPS, ouvrir **Synchronisation**, transférer ce fichier puis lancer **Tester et synchroniser** avec la limite de 50 publications. Le serveur vérifie le format et la présence d'une session non expirée ; seul un passage réel valide l'accès au compte depuis le VPS.

Après un test réussi, activer les passages automatiques. Ils restent actifs tant que le conteneur fonctionne, même si tous les clients web sont fermés et l'ordinateur personnel éteint. Les réglages sont conservés ; au démarrage du service, la planification reprend. Un ancien passage interrompu est marqué comme tel.

Instagram peut expirer la session ou demander une vérification du compte. Dans ce cas, renouveler la connexion puis transférer une nouvelle session. Le fonctionnement sans intervention indéfinie n'est pas établi.

Le bouton **Retirer la session** supprime le fichier du serveur et désactive les passages réguliers. Les fiches de bibliothèque sont conservées. La session n'est jamais incluse dans l'export des fiches.

## Données, arrêt et sauvegardes

| Élément | Emplacement dans le conteneur | Persistance |
| --- | --- | --- |
| Base SQLite | `/app/data/library.sqlite3` | Volume `library_data` |
| Session Instagram | `/app/sessions/instagram.cookies` | Volume `instagram_session` ; fichier en mode 0600 |
| Clé de l'espace privé | `/run/secrets/app_token` | Fichier `secrets/app_token` sur l'hôte |
| Certificats Caddy | `/data` | Volume `caddy_data` |

```sh
docker compose stop
docker compose start
```

Pour une sauvegarde complète, arrêter le service puis sauvegarder le volume de base ; sauvegarder la session séparément si nécessaire. L'export dans l'interface couvre les fiches, leur classement et leurs sources ; les réglages de service, thèmes vides et historiques de traitements ne sont pas restaurés par cet export.

Une mise à jour suit `git pull` puis `docker compose --profile public up -d --build` (retirer le profil pour le mode tunnel). Conserver les volumes et la clé. SQLite et le planificateur sont prévus pour **une seule instance applicative** dans cette version.

## Vérification de l'image

```sh
docker build -t reels-library:dev .
python3 scripts/smoke_container.py
```

Ce test vérifie authentification, utilisateur non root, permissions de session, exclusion de la session des exports et persistance après recréation. Il crée des ressources Docker portant un nom aléatoire, puis les supprime. Il n'utilise aucun véritable compte Instagram.

Références de déploiement : [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/usage.html), [secrets Docker Compose](https://docs.docker.com/compose/how-tos/use-secrets/), [reverse proxy Caddy et HTTPS](https://caddyserver.com/docs/quick-starts/reverse-proxy).
