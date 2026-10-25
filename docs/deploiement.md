# Option : installer sur un NAS ou un serveur

L'installation sur l'ordinateur décrite dans le [README](../README.md) est le parcours principal. Le même conteneur peut tourner sur une autre machine. Les données et la session sont alors stockées sur cette machine, et la synchronisation continue tant qu'elle fonctionne.

## Accès par tunnel SSH

Avec Docker et Compose sur le serveur, récupère le dépôt puis lance :

```sh
docker compose up -d --build
docker compose exec app python -m reels_library.access_key
```

Depuis ton ordinateur, ouvre le tunnel :

```sh
ssh -L 8765:127.0.0.1:8765 utilisateur@adresse-du-serveur
```

Garde ce terminal ouvert et consulte `http://localhost:8765`. Connecte-toi avec `admin` et la clé de cette installation. Aucun Python n'est nécessaire sur l'hôte. Si ton ordinateur utilise déjà le port 8765, arrête son installation locale ou choisis un autre port de tunnel et une origine correspondante.

## Accès HTTPS depuis plusieurs appareils

Fais pointer un domaine sur l'adresse du serveur et autorise les ports 80 et 443. Crée un `.env` dans le dépôt :

```dotenv
REELS_DOMAIN=reels.exemple.fr
REELS_PUBLIC_URL=https://reels.exemple.fr
```

Puis :

```sh
docker compose --profile public up -d --build
docker compose exec app python -m reels_library.access_key
```

Le profil `public` ajoute Caddy et ses volumes de certificats. Ouvre ton adresse HTTPS et utilise `admin` avec la clé. Le port 8765 reste lié à la boucle locale du serveur. Avec un reverse proxy existant, utilise seulement `app`, garde `REELS_PUBLIC_URL` et transmets le domaine dans l'en-tête `Host`.

Le fichier [`.env.example`](../.env.example) est facultatif pour le mode local ; le domaine et `REELS_PUBLIC_URL` sont nécessaires pour l'accès HTTPS. Retire l'origine distante du `.env` lorsque tu reviens à un essai local.

## Session et données

Le [guide Instagram](connexion-instagram.md) explique comment préparer puis importer la session via l'interface. Le backend contacte Instagram depuis la machine qui exécute le conteneur. Une session acceptée sur ton ordinateur peut nécessiter une nouvelle vérification depuis une autre machine ; l'accès effectif reste à tester.

Les volumes `library_data`, `instagram_session` et `app_config` restent sur cet hôte. Pour migrer la bibliothèque, utilise un export des fiches ou une sauvegarde complète des volumes, réalisée application arrêtée. Ne lance pas plusieurs instances sur la même base SQLite.

## Clé gérée par l'administrateur

Le Compose par défaut crée et conserve la clé automatiquement. Un déploiement avancé peut fournir `REELS_ACCESS_TOKEN_FILE` et désactiver `REELS_CREATE_ACCESS_TOKEN`. Le fichier doit être lisible par l'UID 10001 ; garde son répertoire privé. Le script facultatif `scripts/init_secrets.py` prépare un fichier sur l'hôte pour ce cas, mais il n'est plus requis au démarrage standard.

Références : [Docker Compose](https://docs.docker.com/compose/), [Caddy et HTTPS](https://caddyserver.com/docs/automatic-https), [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/usage.html).
