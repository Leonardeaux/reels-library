# Connexion et synchronisation Instagram

[Retour au README](../README.md)

Chaque installation utilise sa propre session. Le conteneur ne lit pas directement les cookies du navigateur de son ordinateur. Python sur l'hôte est nécessaire uniquement pour l'outil facultatif d'export : si tu possèdes déjà un fichier Netscape, passe directement à l'import dans l'application.

## Préparer la connexion Instagram

Cette préparation se fait sur une machine où tu peux te connecter à Instagram dans un navigateur. Elle est nécessaire une première fois, puis à renouveler si Instagram expire la session.

| Élément | Utilité |
| --- | --- |
| `/app/config/app_token` (dans le conteneur) | Te connecter à Reels Library |
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

### Si Chrome sous Windows ne permet pas la lecture

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

Pour renouveler un fichier déjà présent, ajoute `--replace`. Cette préparation avec Firefox sert à créer le fichier utilisé par le conteneur ; tu peux utiliser ton navigateur habituel pour consulter Reels Library.

Pour choisir un profil Chrome précis :

```powershell
.\.venv\Scripts\python.exe -m reels_library.export_session --browser chrome --profile "Profile 1"
```

Remplace `Profile 1` par le nom ou le chemin du profil connecté. Le choix du profil permet de cibler la bonne session ; la possibilité de déchiffrer ses cookies dépend toujours des protections du navigateur.

Si tu disposes déjà d'un fichier de cookies Instagram au format Netscape, tu peux l'utiliser directement pour le transfert suivant.

### Importer la session dans l'application

1. Ouvre ton application sur **http://localhost:8765**, ou à l'adresse de ton installation distante facultative.
2. Va dans **Synchronisation**.
3. Sélectionne le fichier de session et clique sur **Importer la session**.
4. Vérifie que la page indique qu'une session est présente dans le conteneur.

Le fichier est limité à 128 Ko. Le serveur filtre les cookies pour ne conserver que ceux d'Instagram et vérifie la présence d'un cookie de session non expiré. **« Session présente » ne prouve pas encore que le conteneur peut lire les sauvegardes** : c'est le test de synchronisation qui le vérifiera.

Le cookie `sessionid` permet au serveur de réutiliser une connexion Instagram déjà établie. La date du fichier est une expiration déclarée : Instagram peut invalider la session plus tôt. La version actuelle ne renouvelle pas automatiquement le fichier ; il faut le réexporter et le transférer si la connexion cesse d'être acceptée. Les dates Unix en millisecondes présentes dans certains exports sont converties en secondes lors de l'enregistrement, conformément au format Netscape.

Ce fichier donne accès au compte. Conserve-le comme un secret et exclue-le de tes captures, messages de diagnostic et commits. Le dossier `sessions/` est déjà ignoré par Git ; la session stockée dans le conteneur est aussi exclue de l'export des fiches.

## Tester puis activer la synchronisation

### Premier passage manuel

1. Laisse **Activer la synchronisation automatique** décoché pour ce premier test.
2. Choisis **50 · premier test** comme limite.
3. Clique sur **Tester et synchroniser**.
4. Attends que le passage sorte de l'état **En cours**. Le connecteur peut attendre entre les requêtes ; il est arrêté au bout de 15 minutes si le passage n'aboutit pas.
5. Consulte **Derniers passages**, puis ouvre la bibliothèque.

En cas de réussite, le bilan indique le nombre de nouvelles références et de références déjà présentes. Vérifie plusieurs liens et, lorsqu'une légende est présente, compare-la avec la publication source. Les sauvegardes peuvent contenir des publications Instagram autres que des Reels.

En cas d'échec, le message reste dans l'historique. Le serveur conserve les fiches existantes. Un échec peut venir d'une session expirée, d'une vérification demandée par Instagram ou de l'accès depuis l'IP du conteneur.

### Activer les passages réguliers

Après un premier passage réussi :

1. Choisis une fréquence : 15 minutes, 1 heure, 6 heures ou 1 jour.
2. Choisis une limite de lecture : 50, 200, 1 000 ou 5 000 publications.
3. Coche **Activer la synchronisation automatique**, puis clique sur **Enregistrer**.
4. Vérifie la date du prochain passage.

Pour valider le fonctionnement, sauvegarde une nouvelle publication dans Instagram, puis vérifie sa présence après un passage. Tu peux d'abord déclencher **Tester et synchroniser**, puis attendre un passage programmé pour contrôler le planificateur.

**Tu peux fermer l'onglet, mais l'ordinateur qui exécute le conteneur doit rester allumé, avec Docker et l'application démarrés.** Si tu héberges le conteneur sur une autre machine, seul cet hôte doit rester actif. Les erreurs allongent l'attente entre les tentatives ; l'historique permet de suivre ces reprises.

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
