# Contribuer à Reels Library

Le projet est une application web personnelle à installer chez soi, dans un conteneur ou directement avec Python. Les contributions au code du projet sont proposées sous [licence MIT](LICENSE).

Le [guide de développement](docs/developpement.md) explique l'installation et les vérifications. Le [cadrage](docs/cadrage.md), les [décisions](docs/decisions.md) et l'[architecture](docs/architecture.md) décrivent le périmètre et les limites actuelles.

Pour un problème, indique ton système, la version de Docker et Compose, le résultat attendu, le message d'erreur et des étapes de reproduction. Utilise les exemples fictifs du dépôt lorsque possible. Ne joins pas de cookie Instagram, clé d'accès, export de compte ou base personnelle ; les dossiers correspondants sont ignorés par Git.

Pour une modification, conserve les corrections personnelles lors des réimports et la séparation entre bibliothèque et session Instagram. Ajoute des tests lorsqu'un comportement fonctionnel change, puis lance les vérifications adaptées. Un changement du connecteur doit pouvoir être testé avec des réponses simulées, sans connexion à un vrai compte. Une pull request doit expliquer le problème, le comportement obtenu et les vérifications effectuées.

Les noms et adresses e-mail des auteurs et committers font partie de l'historique public. Pour préserver ton adresse personnelle, configure ce dépôt avec l'adresse « noreply » fournie dans les paramètres e-mail de ton compte GitHub avant de créer tes commits. La CI vérifie également tout l'historique avec Gitleaks, en masquant les valeurs détectées dans les journaux.
