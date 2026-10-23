# Architecture de la première version

## Exécution

Un conteneur applicatif Python exécute Waitress, l'application WSGI et un planificateur de synchronisation. Le frontal HTML/CSS/JavaScript est servi par la même application. Un reverse proxy HTTPS peut exposer le service sur un domaine privé avec une clé d'accès personnelle.

La récupération des sauvegardes s'exécute sur le serveur dans un sous-processus `gallery-dl`. Il reçoit le chemin d'un fichier de session, jamais ses valeurs dans les arguments. Le téléchargement des médias est désactivé et les configurations globales du connecteur sont ignorées.

## Modules

| Module | Responsabilité |
| --- | --- |
| `domain.py` | Validation, normalisation des références, recherche sans accents |
| `importers.py` | Lecture ciblée des fichiers et comptabilisation des entrées |
| `database.py` | Base relationnelle, transactions, classement, export |
| `session.py` | Validation, filtrage et écriture atomique de la session |
| `sync.py` | Connecteur, planification, verrou de passage, historique et reprise après erreur |
| `web.py` | API WSGI, contrôle des origines et authentification |
| `__main__.py` | Configuration par environnement et lancement de Waitress |
| `static/` | Bibliothèque et écrans d'import, édition et synchronisation |

## Données

Les références sont uniques par identifiant source Instagram. Les sources sont des enregistrements distincts : entrée importée ou texte fourni manuellement. Les corrections éditoriales restent sur la fiche et un réimport ne les écrase pas. Une nouvelle source importée peut compléter le texte disponible ; un texte corrigé manuellement conserve la priorité.

Les thèmes et collections utilisent des relations multiples. Les étiquettes restent une liste éditoriale. L'état personnel (`to_use`, `in_progress`, `used`, `archived`) est indépendant de la présence technique d'un texte. Aucune analyse IA n'est encore exécutée.

Chaque import conserve un bilan et un état par entrée. La prévisualisation n'écrit rien. Les imports concurrents sont sérialisés avant détection des doublons. Une suppression de référence supprime ses sources et associations ; les compteurs historiques restent disponibles sans conserver le contenu supprimé.

La session Instagram est hors base et hors export. L'API renvoie uniquement sa présence et sa date de transfert. Le connecteur sélectionne explicitement les métadonnées conservées : URL, auteur, légende et date de publication éventuellement disponible. Cette dernière n'est pas assimilée à une date de sauvegarde.

## Synchronisation et limites

- Un seul passage à la fois ; les requêtes web restent disponibles pendant la récupération.
- Fenêtre paramétrable de 50, 200, 1 000 ou 5 000 publications ; limite atteinte signalée.
- Une réponse partielle contenant une erreur est traitée comme un échec, même si le sous-processus sort avec le code zéro.
- Les fiches existantes restent intactes en cas d'échec d'accès. Les erreurs sont présentées sans sortie brute du connecteur.
- Les échecs allongent l'attente entre passages. Le démarrage reprend les réglages persistés et marque les anciens passages inachevés comme interrompus.
- Les retraits dans Instagram ne provoquent pas de suppression locale.
- Pagination historique persistante, synchronisation des suppressions et récupération des collections Instagram restent à développer.
- L'accès réel depuis le VPS nécessite une session valide et une validation sur compte réel.

## Portée actuelle

Usage personnel avec une instance. Une ouverture à plusieurs utilisateurs demanderait des comptes séparés, une isolation des données et des tâches et une évolution du stockage/planificateur. La recherche actuelle charge les références de la bibliothèque en mémoire ; elle sera à mesurer sur le volume réel avant d'introduire un index spécialisé.
