# Développer et vérifier

## Installation Python directe

Python 3.11 ou supérieur est nécessaire pour développer ; il n'est pas requis pour utiliser Docker. Depuis le dépôt, sous Windows :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[sync]"
.\.venv\Scripts\python.exe -m reels_library
```

Sous Linux ou macOS :

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[sync]'
.venv/bin/python -m reels_library
```

Ouvre `http://127.0.0.1:8765`. Garde le terminal ouvert ; `Ctrl+C` arrête le service. `lancer.cmd` facilite les lancements Windows suivants. Ce mode écoute localement et n'exige pas de clé par défaut. Il utilise `data/library.sqlite3` et `sessions/instagram.cookies`, indépendants des volumes Docker.

`requirements.txt` et `requirements-sync.txt` restent disponibles pour les constructions Docker et les installations sans paquet éditable. Le fichier `.env` est lu par Compose ; Python direct lit les variables `REELS_*` déjà présentes dans le terminal.

## Configuration

| Variable | Rôle |
| --- | --- |
| `REELS_HOST`, `REELS_PORT` | Adresse et port du processus Python ; Compose publie son propre port hôte avec `REELS_PORT` |
| `REELS_DATABASE` | Chemin SQLite ; `/app/data/library.sqlite3` dans l'image |
| `REELS_SESSION_FILE` | Fichier Netscape ; `/app/sessions/instagram.cookies` dans l'image |
| `REELS_PUBLIC_URL` | Origine autorisée ; calculée depuis le port local par Compose |
| `REELS_ACCESS_TOKEN_FILE` | Fichier de clé, prioritaire sur `REELS_ACCESS_TOKEN` |
| `REELS_ACCESS_TOKEN` | Clé fournie directement, si aucun fichier n'est configuré |
| `REELS_CREATE_ACCESS_TOKEN` | `true` pour créer une clé absente ; exige un chemin et ne remplace jamais une clé existante |

Un lancement hors boucle locale exige une clé. Une origine distante exige HTTPS. Dans le conteneur, le port interne reste 8080 ; le port hôte est 8765 par défaut.

## Tests

Sous Windows :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Sous Linux ou macOS :

```sh
.venv/bin/python -m unittest discover -v
```

Les tests utilisent des bases temporaires et des réponses simulées. Ils ne lisent pas la véritable session de l'utilisateur et ne contactent pas Instagram.

Pour vérifier aussi le conteneur, avec Docker démarré :

```sh
docker compose config --quiet
docker build -t reels-library:dev .
python scripts/smoke_container.py
```

Sur Linux ou macOS, adapte la dernière commande à ton exécutable Python. Le script crée des ressources Docker aux noms aléatoires, vérifie authentification, exécution non root, permissions, persistance et création automatique de clé, puis nettoie uniquement ses ressources. Il utilise des cookies fictifs et n'envoie aucune requête à Instagram.

Le workflow [Vérifications](../.github/workflows/ci.yml) lance les tests Python sur Windows et Linux, puis construit et vérifie le conteneur Linux. Il ne publie pas d'image ni de release. Une construction réussie ne valide pas l'accès à un compte Instagram réel.

Pour le contrôle fonctionnel dans le navigateur, suis le [test manuel](test-manuel.md). Les sources de l'interface sont directement dans `reels_library/static/`, sans compilation JavaScript.

## Préparer une distribution

Le dépôt est la distribution source. Le rendre public et créer un tag ou une release permet de télécharger ses archives depuis GitHub ; chaque utilisateur construit ensuite son conteneur. Aucun secret ni volume personnel ne doit être inclus. Avant de publier une image préconstruite, vérifie aussi les [notices des dépendances](../THIRD_PARTY_NOTICES.md).
