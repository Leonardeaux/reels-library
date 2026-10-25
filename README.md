# Reels Library — guide de test

Reels Library est une bibliothèque personnelle pour retrouver ses sauvegardes Instagram, les classer et suivre les idées à utiliser. La cible est un **VPS avec Docker**, accessible depuis un ordinateur et un téléphone. Le serveur assure la synchronisation ; ton ordinateur personnel peut être éteint après la connexion initiale.

Ce guide permet de commencer **sans compte Instagram**, avec des exemples fictifs, puis de tester la récupération de tes véritables sauvegardes.

**État actuel :** la bibliothèque et le fonctionnement en conteneur ont été testés. La récupération Instagram réelle depuis un VPS reste à valider avec ton compte. Il n'y a pas encore de transcription, d'analyse IA ni de classement automatique.

## Sommaire

1. [Ce que tu peux tester](#1-ce-que-tu-peux-tester)
2. [Préparer le dépôt et les outils](#2-préparer-le-dépôt-et-les-outils)
3. [Lancer sur ton ordinateur avec Docker](#3-lancer-sur-ton-ordinateur-avec-docker)
4. [Tester la bibliothèque sans Instagram](#4-tester-la-bibliothèque-sans-instagram)
5. [Lancer sur un VPS et accéder depuis le téléphone](#5-lancer-sur-un-vps-et-accéder-depuis-le-téléphone)
6. [Préparer la connexion Instagram](#6-préparer-la-connexion-instagram)
7. [Tester puis activer la synchronisation](#7-tester-puis-activer-la-synchronisation)
8. [Arrêter, redémarrer et conserver les données](#8-arrêter-redémarrer-et-conserver-les-données)
9. [Exécuter les tests automatiques](#9-exécuter-les-tests-automatiques)
10. [Dépannage](#10-dépannage)
11. [Limites et informations utiles pour les retours](#11-limites-et-informations-utiles-pour-les-retours)
12. [Option : lancer sans Docker](#12-option--lancer-sans-docker)

## 1. Ce que tu peux tester

| Fonction | Comportement actuel |
| --- | --- |
| Ajouter un lien | Enregistre une référence Instagram `/reel/`, `/reels/` ou `/p/` et détecte les doublons |
| Importer un fichier | Affiche un aperçu avant enregistrement, puis un bilan des ajouts, doublons, entrées ignorées et erreurs |
| Classer | Plusieurs thèmes, étiquettes et collections personnelles par référence |
| Retrouver | Recherche avec ou sans accents, filtres par thème, suivi, intention, collection et données disponibles |
| Modifier une fiche | Titre, auteur, fiche courte, notes, texte source et classement modifiables |
| Suivre une idée | À utiliser, En cours, Utilisé ou Archivé ; étoile pour la sélection personnelle |
| Conserver la provenance | Sources importées conservées séparément des corrections manuelles |
| Exporter et supprimer | Export réimportable des fiches et suppression d'une référence avec ses sources |
| Synchroniser Instagram | Connecteur expérimental utilisant une session conservée côté serveur ; passages manuels ou réguliers |

Un **lien seul** n'apporte pas automatiquement le contenu de la vidéo. L'indication **Texte disponible** signifie qu'une légende ou un texte a été fourni, sans garantir qu'il décrit tout le contenu du Reel.

## 2. Préparer le dépôt et les outils

Pour le parcours recommandé avec Docker :

- Git pour récupérer et mettre à jour le dépôt privé.
- Docker avec la commande `docker compose`. Sur Windows, Docker Desktop doit être démarré en mode conteneurs Linux.
- Python 3.11 ou supérieur pour les outils de préparation et les tests facultatifs. Le conteneur contient son propre Python.
- Un navigateur pour ouvrir l'application.

Si tu as déjà le dossier du projet, ouvre un terminal dans ce dossier, celui qui contient `compose.yaml`. Pour récupérer les mises à jour :

```sh
git pull --ff-only
```

Si tu pars d'une autre machine, clone le dépôt avec un compte GitHub qui y a accès :

```sh
git clone https://github.com/Leonardeaux/reels-library.git
cd reels-library
```

Vérifie les outils :

```sh
docker --version
docker compose version
```

Sur Windows, vérifie Python avec `python --version`. Sur Linux, utilise `python3 --version`. Les commandes suivantes sont à lancer depuis le dossier du projet, sauf mention contraire.

## 3. Lancer sur ton ordinateur avec Docker

Ce premier essai permet de découvrir l'application avant de l'installer sur un VPS.

### Créer la clé et démarrer

Sous Windows, dans PowerShell :

```powershell
python scripts/init_secrets.py
docker compose up -d --build
docker compose ps
```

Sous Linux :

```sh
python3 scripts/init_secrets.py
docker compose up -d --build
docker compose ps
```

Le premier lancement construit l'image et télécharge ses dépendances. Le service `app` doit apparaître en cours d'exécution, puis `healthy` lorsque le contrôle de disponibilité est passé.

Pour ce test local, tu n'as pas besoin de fichier `.env`. **Si tu en as déjà un provenant d'un déploiement VPS**, vérifie que `REELS_PUBLIC_URL` vaut `http://localhost:8765` pour cet essai.

### Se connecter

Ouvre **http://localhost:8765** dans ton navigateur. La fenêtre de connexion du navigateur demande :

| Champ | Valeur |
| --- | --- |
| Identifiant | `admin` |
| Mot de passe / clé | Contenu du fichier `secrets/app_token` |

Pour lire cette clé toi-même sous Windows :

```powershell
Get-Content .\secrets\app_token
```

Sous Linux :

```sh
cat secrets/app_token
```

Copie la clé sans le retour à la ligne final. Le script d'initialisation conserve la clé lorsqu'elle existe déjà. Garde ce fichier pour les prochains démarrages.

### Vérifier que le serveur répond

Sous PowerShell :

```powershell
Invoke-RestMethod http://localhost:8765/api/health
```

Sous Linux :

```sh
curl -f http://localhost:8765/api/health
```

Le champ `status` doit valoir `ok`. Ce contrôle confirme que le serveur répond ; la connexion Instagram se vérifie plus tard.

## 4. Tester la bibliothèque sans Instagram

### Premier import

1. Clique sur **Importer**.
2. Choisis le fichier [examples/instagram-demo.json](examples/instagram-demo.json) présent dans le dépôt.
3. Clique sur **Vérifier le fichier**.
4. Sur une bibliothèque vide, l'aperçu doit afficher le bilan ci-dessous.
5. Clique sur **Confirmer l'import** : trois fiches apparaissent dans la bibliothèque.

| Résultat attendu au premier import | Nombre |
| --- | ---: |
| À ajouter | 3 |
| Doublons | 1 |
| Ignorées | 1 |
| Erreurs | 1 |
| Entrées comptabilisées | 6 |

L'entrée ignorée est un lien de profil ; l'entrée en erreur contient une date invalide. Elles sont volontairement présentes pour tester le bilan. **Les trois références sont fictives** : leurs liens ne pointent pas vers de véritables vidéos Instagram.

Avant confirmation, aucune référence n'est enregistrée. Après confirmation, le bilan reste consultable dans **Mes imports**.

### Parcours à essayer

| Action | Résultat à vérifier |
| --- | --- |
| Ouvrir une fiche et changer son titre, par exemple en « Crème de test » | Le nouveau titre reste présent après **Enregistrer** puis actualisation de la page |
| Ajouter une note, par exemple « À tester ce week-end » | La note est conservée et permet de retrouver la référence par la recherche |
| Cocher plusieurs thèmes | La même référence est retrouvable dans chacun de ces thèmes |
| Saisir `rapide, test` dans les étiquettes | Deux étiquettes sont enregistrées |
| Saisir `Mes essais` dans les collections | La collection devient disponible dans les filtres |
| Choisir une intention et passer le suivi à **En cours** | Les filtres correspondants retrouvent la fiche |
| Cliquer sur l'étoile | La référence apparaît dans **Ma sélection** |
| Rechercher `creme` après avoir enregistré « Crème de test » | La recherche retrouve le titre malgré l'accent |
| Sur ordinateur, ouvrir le `+` à côté de **THÈMES** | Tu peux créer, renommer ou archiver un thème sans supprimer ses références |
| Ouvrir **Texte et provenance** dans une fiche | Tu peux consulter la source conservée et ajouter ou corriger un texte manuellement |

### Vérifier les doublons et l'export

Sélectionne à nouveau le même fichier de démonstration et clique sur **Vérifier le fichier**. Avec les trois références toujours présentes, le bilan attendu devient **0 ajout, 4 doublons, 1 entrée ignorée et 1 erreur**. Le bouton de confirmation n'est pas proposé lorsqu'il n'y a rien à ajouter.

Clique sur **Exporter ma bibliothèque** : le navigateur télécharge `reels-library.json`. Ce fichier contient les fiches, leur classement, leurs notes et leurs sources. Il peut être réimporté dans une autre instance vide. Dans une bibliothèque qui contient déjà les références, les doublons conservent leurs corrections actuelles.

Pour nettoyer l'essai, ouvre chaque fiche fictive et utilise **Supprimer la référence**. **Archivé** permet plutôt de conserver une fiche avec ce suivi personnel.

### Essayer avec un véritable lien ou export

- **Ajouter un Reel** : colle le lien d'une publication Instagram, puis donne-lui un titre et des notes si tu le souhaites. Cet ajout seul ne récupère pas la vidéo.
- **Importer** : utilise un JSON de sauvegardes ou un fichier `.txt` contenant un lien par ligne.
- Les JSON reconnus contiennent une liste d'objets, ou une liste sous `saved_saved_media`, `saved_media`, `saved_posts` ou `items`. L'export de Reels Library est également reconnu.
- Les archives ZIP et les exports HTML ne sont pas pris en charge. Extrais l'archive et sélectionne le fichier JSON utile.
- L'interface limite le fichier d'import à 10 Mo. Le format exact de ton export réel reste à vérifier ; le bilan indique les entrées non exploitables.

## 5. Lancer sur un VPS et accéder depuis le téléphone

Les commandes de lancement doivent être exécutées **sur le VPS**. Le dossier cloné sur ce serveur devient son propre déploiement ; les données de ton essai Docker local ne s'y transfèrent pas automatiquement. Utilise l'export des fiches si tu veux les reprendre.

### Premier essai sur VPS, sans domaine

Sur le VPS, clone le dépôt, crée la clé et démarre l'application :

```sh
python3 scripts/init_secrets.py
docker compose up -d --build
```

Sur ton ordinateur client, ouvre un tunnel vers le VPS en remplaçant l'utilisateur et l'adresse :

```sh
ssh -L 8765:127.0.0.1:8765 utilisateur@adresse-du-vps
```

Garde ce terminal ouvert pour accéder à **http://localhost:8765**. Utilise la clé `secrets/app_token` **du VPS**. Si ton essai Docker local utilise déjà le port 8765, arrête-le avant d'ouvrir ce tunnel.

Le tunnel donne accès à l'interface ; les synchronisations sont exécutées par le VPS et continuent après sa fermeture.

### Accès habituel en HTTPS, sur ordinateur et téléphone

1. Fais pointer un domaine ou sous-domaine vers l'IP du VPS.
2. Autorise les ports 80 et 443 dans son pare-feu.
3. Crée un fichier `.env` dans le dépôt sur le VPS avec tes véritables valeurs :

```dotenv
REELS_DOMAIN=reels.exemple.fr
REELS_PUBLIC_URL=https://reels.exemple.fr
```

4. Lance le profil qui inclut le reverse proxy HTTPS :

```sh
docker compose --profile public up -d --build
docker compose --profile public ps
```

5. Ouvre ton adresse HTTPS depuis l'ordinateur puis le téléphone. Connecte-toi sur chaque appareil avec `admin` et la clé du VPS.

Caddy gère HTTPS. Si tu as déjà un reverse proxy, consulte le [guide de déploiement](docs/deploiement.md). Le port 8765 reste publié uniquement sur la boucle locale du serveur ; il n'est pas nécessaire de l'ouvrir à Internet.

## 6. Préparer la connexion Instagram

Cette préparation se fait sur une machine où tu peux te connecter à Instagram dans un navigateur. Elle est nécessaire une première fois, puis à renouveler si Instagram expire la session.

| Élément | Utilité |
| --- | --- |
| `secrets/app_token` | Te connecter à Reels Library |
| `sessions/instagram.cookies` préparé ci-dessous | Permettre au serveur de lire les sauvegardes du compte Instagram connecté |

### Créer le fichier de session

Connecte-toi d'abord à **https://www.instagram.com/** dans le navigateur choisi et vérifie que tu peux consulter tes sauvegardes. Le profil est sélectionné automatiquement par le connecteur ; l'option `--profile` permet de choisir un profil précis si plusieurs existent.

Sur **ton ordinateur Windows**, depuis le dépôt, prépare l'outil :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-sync.txt
```

Puis exporte la session du navigateur connecté. Exemple pour Edge :

```powershell
.\.venv\Scripts\python.exe -m reels_library.export_session --browser edge
```

Remplace `edge` par `chrome` ou `firefox` selon ton navigateur. Sur Linux, les commandes équivalentes sont :

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-sync.txt
.venv/bin/python -m reels_library.export_session --browser firefox
```

Le fichier produit est **`sessions/instagram.cookies`**. L'outil ne contacte pas Instagram pour établir une nouvelle connexion : il lit la session du navigateur déjà connecté. La lecture peut échouer selon le profil et les protections du navigateur ; le message d'erreur sera affiché sans les valeurs des cookies.

#### Si Chrome sous Windows ne permet pas la lecture

Depuis Chrome 127, Google a introduit le chiffrement **App-Bound Encryption**, qui lie le déchiffrement des cookies à Chrome. Le connecteur `gallery-dl` 1.32.17 utilisé ici ne gère pas ce chiffrement dans son lecteur de cookies Windows. C'est une cause possible d'échec de `--browser chrome`. [Explication officielle de Google](https://security.googleblog.com/2024/07/improving-security-of-chrome-cookies-on.html).

L'outil distingue désormais les cas suivants :

| Code d'erreur | Action proposée |
| --- | --- |
| `COOKIES_LOCKED` | Ferme complètement le navigateur puis relance avec ton compte Windows habituel |
| `COOKIES_DECRYPTION_FAILED` | Prépare la session dans Firefox : connecte-toi à Instagram dans Firefox, puis lance la commande ci-dessous |
| `COOKIES_PROFILE_NOT_FOUND` | Vérifie le navigateur installé et précise le profil avec `--profile` |
| `INSTAGRAM_SESSION_MISSING` | Vérifie que le profil choisi est connecté au compte Instagram voulu |
| `COOKIES_READ_FAILED` | La cause n'a pas pu être précisée ; conserve ce code et les étapes de reproduction pour le diagnostic |
| `SESSION_WRITE_FAILED` | Vérifie les permissions du dossier de sortie ou choisis un autre chemin avec `--output` |

Exemple Windows, après connexion à Instagram dans Firefox :

```powershell
.\.venv\Scripts\python.exe -m reels_library.export_session --browser firefox
```

Pour renouveler un fichier déjà présent, ajoute `--replace`. Cette préparation avec Firefox sert à créer le fichier utilisé par le VPS ; tu peux utiliser ton navigateur habituel pour consulter Reels Library.

Pour choisir un profil Chrome précis :

```powershell
.\.venv\Scripts\python.exe -m reels_library.export_session --browser chrome --profile "Profile 1"
```

Remplace `Profile 1` par le nom ou le chemin du profil connecté. Le choix du profil permet de cibler la bonne session ; la possibilité de déchiffrer ses cookies dépend toujours des protections du navigateur.

Si tu disposes déjà d'un fichier de cookies Instagram au format Netscape, tu peux l'utiliser directement pour le transfert suivant.

### Transférer la session vers l'application

1. Ouvre ton application, en HTTPS sur le VPS, ou via l'accès local/tunnel décrit plus haut.
2. Va dans **Synchronisation**.
3. Sélectionne le fichier de session et clique sur **Transférer la session**.
4. Vérifie que la page indique qu'une session est présente sur le serveur.

Le fichier est limité à 128 Ko. Le serveur filtre les cookies pour ne conserver que ceux d'Instagram et vérifie la présence d'un cookie de session non expiré. **« Session présente » ne prouve pas encore que le VPS peut lire les sauvegardes** : c'est le test de synchronisation qui le vérifiera.

Le cookie `sessionid` permet au serveur de réutiliser une connexion Instagram déjà établie. La date du fichier est une expiration déclarée : Instagram peut invalider la session plus tôt. La version actuelle ne renouvelle pas automatiquement le fichier ; il faut le réexporter et le transférer si la connexion cesse d'être acceptée. Les dates Unix en millisecondes présentes dans certains exports sont converties en secondes lors de l'enregistrement, conformément au format Netscape.

Ce fichier donne accès au compte. Conserve-le comme un secret et exclue-le de tes captures, messages de diagnostic et commits. Le dossier `sessions/` est déjà ignoré par Git ; la session stockée sur le serveur est aussi exclue de l'export des fiches.

## 7. Tester puis activer la synchronisation

### Premier passage manuel

1. Laisse **Activer la synchronisation automatique** décoché pour ce premier test.
2. Choisis **50 · premier test** comme limite.
3. Clique sur **Tester et synchroniser**.
4. Attends que le passage sorte de l'état **En cours**. Le connecteur peut attendre entre les requêtes ; il est arrêté au bout de 15 minutes si le passage n'aboutit pas.
5. Consulte **Derniers passages**, puis ouvre la bibliothèque.

En cas de réussite, le bilan indique le nombre de nouvelles références et de références déjà présentes. Vérifie plusieurs liens et, lorsqu'une légende est présente, compare-la avec la publication source. Les sauvegardes peuvent contenir des publications Instagram autres que des Reels.

En cas d'échec, le message reste dans l'historique. Le serveur conserve les fiches existantes. Un échec peut venir d'une session expirée, d'une vérification demandée par Instagram ou de l'accès depuis l'IP du VPS.

### Activer les passages réguliers

Après un premier passage réussi :

1. Choisis une fréquence : 15 minutes, 1 heure, 6 heures ou 1 jour.
2. Choisis une limite de lecture : 50, 200, 1 000 ou 5 000 publications.
3. Coche **Activer la synchronisation automatique**, puis clique sur **Enregistrer**.
4. Vérifie la date du prochain passage.

Pour valider le fonctionnement, sauvegarde une nouvelle publication dans Instagram, puis vérifie sa présence après un passage. Tu peux d'abord déclencher **Tester et synchroniser**, puis attendre un passage programmé pour contrôler le planificateur.

**Ton ordinateur peut ensuite être éteint.** Le VPS doit rester actif, Docker démarré et le conteneur en cours d'exécution. Les erreurs allongent l'attente entre les tentatives ; l'historique permet de suivre ces reprises.

### Limites à connaître pendant ce test

- La lecture porte sur une fenêtre de publications renvoyées par Instagram. Une limite atteinte est signalée. Relancer avec la même limite ne parcourt pas automatiquement tout l'historique ancien.
- Un nouveau passage déduplique les références et conserve tes corrections personnelles. Il peut ajouter une nouvelle source textuelle à une référence existante.
- Retirer une sauvegarde dans Instagram ne supprime pas sa fiche dans Reels Library.
- Le serveur récupère des références et les métadonnées accessibles, sans télécharger les vidéos ni les analyser.

### Renouveler ou retirer la session

Si Instagram demande une nouvelle connexion, reconnecte-toi au compte puis relance l'outil avec `--replace`. Exemple Windows pour Edge :

```powershell
.\.venv\Scripts\python.exe -m reels_library.export_session --browser edge --replace
```

Transfère le nouveau fichier dans l'application et teste un passage. Pour déconnecter le service, utilise **Retirer la session** : le fichier du serveur est supprimé et la synchronisation automatique désactivée, tandis que tes fiches restent présentes.

## 8. Arrêter, redémarrer et conserver les données

Commandes à lancer sur la machine qui héberge Docker, depuis le dépôt :

| Besoin | Commande |
| --- | --- |
| Vérifier l'état | `docker compose ps` |
| Consulter les journaux applicatifs | `docker compose logs --tail=100 app` |
| Redémarrer l'application | `docker compose restart app` |
| Arrêter l'application | `docker compose stop app` |
| La relancer | `docker compose start app` |
| Arrêter et retirer les conteneurs, en conservant les volumes | `docker compose down` |
| Relancer après `down` | `docker compose up -d` ou, pour HTTPS, `docker compose --profile public up -d` |

Pour arrêter également le proxy d'un déploiement HTTPS, utilise `docker compose --profile public down`.

**N'ajoute pas `--volumes` à `down` si tu souhaites conserver les données** : cette option supprime les volumes persistants du projet.

| Donnée | Stockage dans le déploiement Docker |
| --- | --- |
| Fiches, sources, classement, réglages et historiques | Volume `library_data` ; base `/app/data/library.sqlite3` |
| Session Instagram | Volume `instagram_session` ; fichier `/app/sessions/instagram.cookies` |
| Clé de connexion à l'application | `secrets/app_token` sur l'hôte |
| Certificats HTTPS | Volume `caddy_data` lorsque le proxy est utilisé |

Pour vérifier la persistance toi-même, modifie une fiche, redémarre `app`, attends qu'il réponde puis recharge la page : la fiche et tes réglages doivent rester présents.

L'export depuis l'interface sauvegarde les fiches et leurs sources. Il ne restaure pas les historiques, les réglages du service, la session Instagram ni les thèmes sans référence. Pour une sauvegarde complète, arrête le service puis sauvegarde les volumes et la clé, en conservant la session séparément.

Pour mettre à jour le code sur le VPS :

```sh
git pull --ff-only
docker compose --profile public up -d --build
```

Retire `--profile public` pour un déploiement utilisé uniquement par tunnel SSH. Conserve les volumes et le fichier de clé.

## 9. Exécuter les tests automatiques

Depuis le dépôt, sur une machine avec Python 3.11 ou supérieur :

```sh
python -m unittest discover -v
```

Sous Linux, remplace `python` par `python3`. La suite actuelle contient **56 tests**. Ils doivent se terminer par **OK**. Ils utilisent des bases temporaires et des réponses Instagram simulées, sans lire ta véritable session ni connecter ton compte.

Pour tester aussi l'image Docker :

```sh
docker build -t reels-library:dev .
python scripts/smoke_container.py
```

Ce test vérifie l'accès privé, l'exécution sans root, la séparation de la session et la persistance après recréation d'un conteneur. Il crée puis supprime ses propres conteneurs et volumes éphémères. Il ne modifie pas les volumes du déploiement Compose et n'appelle pas Instagram.

## 10. Dépannage

| Symptôme | Vérification ou action |
| --- | --- |
| `docker` ou `docker compose` introuvable | Vérifie l'installation de Docker et la disponibilité de Compose dans ce terminal |
| Impossible de joindre le moteur Docker | Démarre Docker Desktop sur Windows, ou le service Docker sur le VPS |
| `python` introuvable | Sous Linux, essaie `python3` ; sous Windows, vérifie l'installation et le chemin de Python |
| Fichier `secrets/app_token` absent | Exécute `python scripts/init_secrets.py`, ou `python3` sous Linux, avant de relancer Compose |
| Page inaccessible | Vérifie `docker compose ps`, le contrôle `/api/health` et `docker compose logs --tail=100 app` |
| Port 8765 déjà utilisé | Arrête l'autre essai local ou le tunnel qui utilise ce port avant de relancer le parcours choisi |
| La connexion demande sans cesse un mot de passe | Utilise `admin` et la clé de la machine qui héberge cette instance ; recopie la clé sans retour à la ligne |
| Erreur **Hôte non autorisé** ou **origine non autorisée** | Vérifie que `REELS_PUBLIC_URL` correspond à l'adresse utilisée. Après modification de `.env`, relance `docker compose up -d` avec le profil approprié |
| HTTPS ne fonctionne pas | Vérifie DNS, ports 80/443 et `docker compose --profile public logs --tail=100 proxy` ; consulte aussi le guide VPS |
| L'application n'est pas accessible sur le téléphone par `localhost` | `localhost` désigne le téléphone lui-même. Utilise l'adresse HTTPS du VPS |
| L'export de session échoue | Consulte le code d'erreur et le tableau de la section 6 ; utilise `--profile` pour cibler le bon profil |
| Chrome renvoie `COOKIES_DECRYPTION_FAILED` sous Windows | La protection App-Bound peut empêcher le déchiffrement ; prépare la session en te connectant à Instagram dans Firefox puis avec `--browser firefox` |
| L'outil dit que le fichier de session existe déjà | Ajoute `--replace` uniquement lorsque tu veux renouveler cette session |
| Aucune session Instagram valide dans le fichier | Fournis un export Netscape contenant une session Instagram non expirée ; reconnecte-toi avant de le renouveler |
| Session présente, mais synchronisation en échec | Consulte le dernier passage et vérifie le compte Instagram pour une demande de vérification ; renouvelle la session si nécessaire |
| Instagram limite les requêtes | Attends avant une nouvelle tentative ; évite les relances répétées et consulte la prochaine date prévue |
| Pas de passage automatique | Vérifie activation, prochain passage, validité de la session et état du conteneur ; le navigateur ouvert seul ne lance pas le service |
| Des sauvegardes anciennes manquent | Vérifie si la limite de lecture a été atteinte ; la reprise historique paginée reste à développer |
| Import refusé | Utilise le JSON des sauvegardes ou un texte avec un lien par ligne ; ZIP, HTML et structures inconnues sont refusés |
| Pas de résumé ou de recette générée | Les fiches courtes sont encore manuelles ; l'analyse IA fait partie des étapes suivantes |

## 11. Limites et informations utiles pour les retours

Cette version vise un usage personnel et **une seule instance applicative**. Le compte est protégé par une clé commune ; il n'y a pas encore de comptes utilisateurs distincts. L'accès Instagram réel, sa stabilité depuis un VPS et la couverture des contenus privés ou supprimés doivent être évalués pendant ton essai.

L'interface est adaptée aux petits écrans, mais sa vérification visuelle sur tes appareils reste à faire. Le premier module spécialisé, la transcription et l'analyse IA seront choisis après validation de la bibliothèque et de la récupération.

Pour signaler un problème, les informations utiles sont :

- le parcours utilisé : Docker local, VPS par tunnel, ou VPS en HTTPS ;
- l'appareil, le navigateur et les étapes pour reproduire ;
- le résultat attendu et le message d'erreur exact ;
- pour un import, les compteurs du bilan ; pour la synchronisation, l'état du dernier passage ;
- si nécessaire, les dernières lignes pertinentes de `docker compose logs --tail=100 app`.

Partage des exemples anonymisés et masque la clé d'accès, les fichiers de session et les données personnelles.

## 12. Option : lancer sans Docker

Ce mode permet de tester le code sur ton ordinateur. Depuis le dépôt, sous Windows :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-sync.txt
.\.venv\Scripts\python.exe -m reels_library
```

Sous Linux :

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-sync.txt
.venv/bin/python -m reels_library
```

Ouvre **http://127.0.0.1:8765**. Garde le terminal ouvert ; `Ctrl+C` arrête le service. Sous Windows, `lancer.cmd` facilite les lancements suivants après installation des dépendances.

Le lancement local par défaut n'exige pas de clé et écoute seulement sur la boucle locale. Les données vont dans `data/library.sqlite3` et la session dans `sessions/instagram.cookies` : ces fichiers sont distincts des volumes Docker. Le fichier `.env` est pris en compte par Compose ; le lancement Python direct utilise les variables d'environnement `REELS_*` déjà définies dans ton terminal.

Pour un autre port local, tu peux ajouter `--port 8766` à la commande de lancement, puis ouvrir l'adresse correspondante. Pour un déploiement distant, suis le parcours Docker et HTTPS ci-dessus.

## Documentation complémentaire

- [Déploiement VPS détaillé](docs/deploiement.md)
- [Architecture et limites techniques](docs/architecture.md)
- [Décisions et préférences confirmées](docs/decisions.md)
- [Prochaines étapes](docs/prochaines-etapes.md)
- [Cadrage initial](docs/cadrage.md)
