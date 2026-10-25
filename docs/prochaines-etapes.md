# Prochaines étapes

## Base disponible

Application personnelle auto-hébergée, installation Docker sans Python sur l'hôte, clé créée au démarrage, stockage persistant séparé, bibliothèque, recherche, classement, import/export et connecteur expérimental. Code du projet sous MIT, documentation utilisateur et contribution, vérifications Python et Docker sur GitHub.

## 1. Valider un parcours utilisateur complet

Depuis une archive GitHub neuve, lancer Docker sur un ordinateur sans environnement de développement, retrouver la clé, importer la démonstration et vérifier les mises à jour sans perte de données. Essayer Windows, macOS et Linux. Vérifier visuellement le parcours dans les navigateurs réels.

## 2. Valider puis fiabiliser Instagram

Tester 30 à 50 sauvegardes sur un compte réel : légendes, dates, contenus privés ou supprimés, temps de traitement, expiration et vérifications demandées par Instagram. Aucun compte réel n'a été utilisé pour les tests automatisés.

Ajouter ensuite pagination et point de reprise pour l'historique. La version actuelle relit une fenêtre limitée et déduplique. Le renouvellement de session reste manuel, et les retraits Instagram ne suppriment pas les fiches locales.

## 3. Faciliter la connexion

Améliorer la préparation d'une session sans environnement Python, les indications de renouvellement et le diagnostic des navigateurs. Conserver une action volontaire de l'utilisateur et ne pas distribuer de cookie dans le code ou les exemples.

## 4. Étudier une distribution préconstruite

Une image prête à télécharger pourrait réduire le temps du premier lancement. Il faut alors prévoir versions, mises à jour, architectures supportées et notices des dépendances. Une application native ou un installateur n'est pas requis pour le parcours conteneur retenu.

## 5. Ajouter l'analyse et les modules spécialisés

Quand les sources sont accessibles, mesurer la qualité et le coût des transcriptions et analyses. Conserver leur provenance et les informations manquantes. Choisir ensuite le premier module : recettes, veille ou projets DIY.
