# Cadrage initial — Bibliothèque active de Reels

Version 0.2 — 23 octobre 2026. Titre de travail.

Ce document prépare les décisions. Les propositions restent à discuter ; la récupération Instagram n'a pas encore été testée sur un compte réel.

## Vision et décisions

Transformer les Reels sauvegardés en informations faciles à retrouver et en ressources utilisables : recettes, fiches de veille, projets à réaliser et futurs formats spécialisés.

Le produit couvre quatre besoins : récupérer, comprendre, retrouver et utiliser. Sa valeur se mesurera au temps gagné et aux ressources effectivement utilisées.

| Élément | État |
| --- | --- |
| Usage personnel, ouverture possible ensuite | Confirmé par l'utilisateur |
| Reels sauvegardés comme source initiale | Demandé |
| Catégories évolutives | Demandé |
| Cuisine, informatique/IA/data/robotique, making/DIY/impression 3D | Exemples initiaux, liste ouverte |
| Bibliothèque commune et modules spécialisés | Proposition |
| Premier module, supports, budget et calendrier | À préciser |
| Synchronisation automatique des sauvegardes | Faisabilité non établie |
| Parcours sans Hermes ni iMessage | Préférence exprimée par l'utilisateur |

## Récupération : première validation

Les API Instagram présentées par Meta visent les comptes professionnels ; la variante avec Facebook Login exclut les comptes personnels. Les capacités documentées consultées ne fournissent pas de voie pour synchroniser leurs sauvegardes. Conclusion de cadrage : ne pas promettre cette synchronisation. [API Meta, Facebook Login](https://www.postman.com/meta/instagram/folder/u4g5a2a/instagram-api-with-facebook-login), [API Meta, Instagram Login](https://www.postman.com/meta/instagram/folder/6raa77c/instagram-api-with-instagram-login).

Meta propose un export des informations Instagram dans l'Espace Comptes. Cette source confirme le mécanisme, pas le contenu exact d'un export de sauvegardes. Un export réel devra être examiné. [Présentation officielle Meta](https://about.fb.com/news/2023/10/manage-your-information-across-apps/).

Vérification documentaire : 23 octobre 2026. Les pages développeur Meta et l'aide Instagram ouvertes directement ont renvoyé une erreur 429 ; les informations sur les API proviennent de la collection publiée par Meta sur Postman. Aucun compte Instagram n'a été connecté.

| Besoin | Piste | À vérifier |
| --- | --- | --- |
| Reprendre l'historique | Import d'un export demandé par l'utilisateur | Sauvegardes incluses, liens, dates, collections, légendes ; différences HTML/JSON |
| Ajouter de nouveaux Reels | Coller un lien ; étudier le partage depuis le téléphone | Informations transmises et parcours iOS/Android |
| Analyser en profondeur | Texte, audio et images effectivement disponibles | Accès, conditions d'utilisation, stabilité et coût |
| Synchroniser automatiquement | Étude technique distincte | Mécanisme adapté et fiabilité |

Importer une référence, récupérer son contenu et l'analyser sont trois opérations différentes. Un lien seul ne permet pas de garantir un résumé, une recette ou une fiche projet.

Une automatisation utilisant une session Instagram serait une piste distincte, avec maintenance et dépendance au compte à évaluer. Elle ne constitue pas une capacité validée.

Essai proposé sur 30 à 50 sauvegardes représentatives :

1. Examiner l'export et comptabiliser chaque entrée.
2. Mesurer les données disponibles : lien seul, texte, audio, images ou vidéo.
3. Inclure des Reels privés, supprimés, multilingues, sans parole ou incomplets.
4. Mesurer couverture, temps et coût.
5. Définir les promesses possibles du MVP.

Un essai sur des vidéos fournies manuellement peut évaluer l'analyse ; il ne prouve pas l'acquisition automatique. Si seuls des liens sont accessibles, décider entre enrichissement manuel et poursuite du travail d'acquisition avant de développer l'ensemble du produit.

## Usages et modules

| Module | Résultat attendu | Extensions possibles |
| --- | --- | --- |
| Bibliothèque | Rechercher une idée sans connaître l'auteur ni la date | Recherche par sens si les filtres et le texte ne suffisent pas |
| Cuisine | Fiche recette modifiable avec ingrédients, quantités présentes, étapes et manques | Portions, courses, menus, export vers une application existante |
| Informatique et veille | Fiche des sujets, outils, concepts et liens cités ; regroupement par sous-thème | Synthèses datées, sources externes, contrôle de fraîcheur |
| Making / DIY / 3D | Fiche avec matériel, outils, prérequis, étapes et fichiers présents | Suivi de réalisation, inventaire, budget estimé explicitement |
| Futurs modules | Formats définis selon de nouveaux besoins | Autres domaines à préciser |

La veille sur les contenus sauvegardés et la découverte d'informations nouvelles sont deux fonctions distinctes. La seconde nécessite d'autres sources et un contrôle de leur fraîcheur. Résumer une ancienne vidéo ne suffit pas à vérifier une information actuelle.

Un Reel peut alimenter plusieurs modules ; une fiche peut regrouper plusieurs Reels en conservant leur provenance.

Pour reprendre une application de recettes, comparer ses fonctions, ses imports/exports, ses possibilités d'intégration, son coût et sa gestion des informations incomplètes. Aucun outil n'est encore choisi.

## Classement évolutif

Séparer trois dimensions :

| Dimension | Exemples |
| --- | --- |
| Sujet et sous-catégories | Cuisine, IA, robotique, impression 3D |
| Nature du contenu | Tutoriel, démonstration, actualité, opinion, inspiration |
| Intention personnelle | À apprendre, à cuisiner, à fabriquer, référence |

Un bras robotique imprimé en 3D peut relever de la robotique et de l'impression 3D, avec l'intention « À fabriquer ».

Règles proposées :

- Plusieurs catégories et étiquettes par Reel.
- Création, renommage, fusion et archivage sans perte de contenu.
- Réutilisation des catégories existantes ; validation des nouvelles propositions de l'IA pour éviter leur multiplication.
- État « À classer » lorsque les données manquent.
- Corrections personnelles conservées lors d'une nouvelle analyse.
- Collections personnelles, par exemple « Projets été », distinctes des thèmes.
- Modules déclenchés selon le contenu et l'intention, sans correspondance rigide avec un dossier.

## Analyse et fiabilité

Chaîne proposée : réception → normalisation du lien → doublons → acquisition → extraction → classement et résumé → recherche → modules spécialisés.

L'extraction peut combiner légende, transcription audio, texte à l'écran et images sélectionnées, selon leur disponibilité.

Principes :

- Afficher les sources utilisées et relier les champs importants à leur provenance.
- Séparer information extraite, déduction et suggestion complémentaire.
- Laisser inconnue une quantité, température, durée, valeur ou référence absente.
- Permettre correction et relance d'une étape sans écraser les modifications personnelles.
- Distinguer résumé fidèle et vérification des affirmations.
- Traiter les instructions présentes dans les contenus comme des données, sans les laisser piloter l'application.

Chaque module définit ses critères de complétude. Une inspiration culinaire sans quantités reste utile sans être présentée comme une recette complète.

## Première version utile proposée

- Import par la méthode validée, avec bilan : nouvelles entrées, doublons et erreurs.
- Ajout manuel par lien.
- Classement et résumé lorsque les données le permettent.
- Recherche, filtres, fiche courte et retour à la source.
- Correction du classement et des résultats.
- Intention et suivi : « À utiliser », « En cours », « Utilisé », « Archivé ».
- Sélection courte pour retrouver des ressources pertinentes.
- Export et suppression des données.

Ajouter un premier module spécialisé pour valider la valeur de bout en bout. Le choix du module reste ouvert.

Reporter les trois modules complets, les recommandations avancées, la découverte externe et l'ouverture au public jusqu'aux premiers retours. La synchronisation automatique reste une étude de faisabilité.

Tester le partage depuis le téléphone avant de choisir entre site adapté au mobile, application installable et application native.

## Redécouverte et passage à l'action

Parcours : importer → retrouver → consulter la fiche → cuisiner, apprendre ou fabriquer → marquer l'utilisation.

Une sélection limitée, par exemple trois ressources sur demande, est une hypothèse à tester. Elle peut tenir compte des projets en cours, des intentions et des contenus déjà utilisés. L'utilisateur doit pouvoir indiquer explicitement ce qui est important pour lui.

Notifications et synthèses périodiques restent des options du futur produit. Aucune automatisation n'est créée par ce cadrage.

## Architecture de principe

Proposition pour l'usage personnel : application organisée en modules, base relationnelle et analyses en arrière-plan. Le choix des technologies suivra les essais d'accès aux données et les contraintes du support.

| Ensemble | Responsabilité |
| --- | --- |
| Interface | Import, bibliothèque, recherche, catégories, fiches et suivi |
| Connecteurs | Exports, liens et fichiers éventuellement fournis |
| Traitements en arrière-plan | Acquisition, extraction, analyse et reprise des erreurs |
| Base de données | Références, classement, analyses, fiches et préférences |
| Stockage de fichiers si nécessaire | Sources utiles et médias disponibles, avec conservation définie |
| Modules | Formats métier et échanges avec d'autres outils |

Prévoir des données distinctes pour les références, sources, classements, analyses versionnées, fiches métier, suivi personnel et tâches d'import.

Conserver URL normalisée et identifiant source si connu ; distinguer dates de publication, sauvegarde, import et analyse. Une relance doit réutiliser les étapes déjà effectuées.

Séparer l'état technique (« en attente », « terminé », « données insuffisantes », « erreur ») de l'état personnel (« à essayer », « en cours », « utilisé »).

Ce découpage doit permettre de changer l'acquisition ou le service d'analyse sans reconstruire les modules.

## Coût et exploitation

Mesurer séparément coût initial de l'historique et coût récurrent des ajouts, retraitements et hébergement. Le volume, la durée des vidéos et la profondeur d'analyse détermineront l'essentiel du coût variable.

Prévoir aperçu avant analyse massive, détection des doublons et réutilisation des résultats.

Décider où les données sont conservées, lesquelles sont envoyées au service d'analyse et comment les exporter, supprimer et sauvegarder. Limiter l'import aux fichiers utiles plutôt que conserver tout un export de compte. Séparer les clés techniques des données.

L'ouverture à d'autres utilisateurs nécessitera notamment authentification, séparation des données et revue des conditions et obligations applicables avant lancement.

## Validation proposée

Ces objectifs sont à confirmer ; aucune performance n'a encore été mesurée.

| Dimension | Critère de travail |
| --- | --- |
| Import | Chaque entrée est comptabilisée : importée, doublon, ignorée avec motif ou en erreur |
| Réimport | Le même fichier ne crée pas de doublons de références |
| Couverture | Mesurer liens seuls, entrées avec texte et contenus analysables en profondeur |
| Classement | Viser 80 % de classements jugés utiles sur un lot évalué manuellement |
| Recherche | Retrouver le contenu attendu en moins de 30 secondes dans au moins huit recherches représentatives sur dix |
| Extraction | Vérifier les champs renseignés ; distinguer exactitude et complétude ; relever tout champ inventé comme défaut |
| Coût | Mesurer séparément texte et analyse avec audio/images |
| Utilité | Après deux semaines d'essai, observer ressources retrouvées, fiches utilisées et temps de correction |

Inclure les contenus privés, supprimés ou incomplets dans le bilan de couverture pour ne pas masquer les limites du parcours.

## Étapes suivantes

| Étape | Livrable |
| --- | --- |
| Préciser l'usage | Volume, appareils, priorité et contraintes |
| Tester l'acquisition | Données accessibles, couverture et coût sur un lot réel |
| Définir les fiches | Exemples attendus dans chaque catégorie |
| Délimiter le MVP | Parcours, écrans essentiels, premier module et critères |
| Choisir la solution technique | Architecture concrète et estimation après validation des inconnues |
| Prototyper et essayer | Parcours complet puis retours sur deux semaines |

Questions ouvertes :

1. Quel usage valider en premier : bibliothèque, cuisine, veille ou DIY ?
2. Combien de sauvegardes existent et combien s'ajoutent par semaine ?
3. Quels supports : Android, iPhone, ordinateur ?
4. Un import initial puis des ajouts par lien conviennent-ils au départ, ou la synchronisation est-elle indispensable ?
5. Quel budget mensuel et quelles préférences de traitement local ou en ligne ?
6. Quels outils de recettes, notes ou projets faut-il conserver dans le parcours ?

La prochaine décision porte sur la priorité et le niveau d'automatisation indispensable. Le premier travail technique sera la preuve d'accès aux données, avant de figer les technologies et le calendrier.

## Référence technique étudiée : reels-vault

Le 23 octobre 2026, examen statique du [README](https://github.com/sosoj92/reels-vault), de [ingest.py](https://github.com/sosoj92/reels-vault/blob/main/ingest.py), de [graphe.py](https://github.com/sosoj92/reels-vault/blob/main/graphe.py) et de la [licence](https://github.com/sosoj92/reels-vault/blob/main/LICENSE). Aucun script exécuté et aucun accès à une session Instagram. La consultation du code ne vaut pas validation de son fonctionnement actuel.

Cette référence donne une piste concrète pour le prototype d'acquisition. La synchronisation des sauvegardes reste à établir.

Propositions issues de cette comparaison, à valider :

- Évaluer séparément un moteur d'ingestion et de transcription réutilisable.
- Prévoir une interface propre pour l'import et la consultation.
- Garder le service d'analyse interchangeable.
- Conserver les sources brutes et produire des fiches structurées pour les modules métier.
- Distinguer réussite technique, contenu partiellement récupéré et résultat exploitable.
- Tester plusieurs stratégies de lecture des images sur des recettes et des tutoriels.
- Conserver les collections et dates présentes dans l'export lorsque disponibles.
- Normaliser les références avant détection des doublons.
- Maintenir les catégories et corrections dans la bibliothèque.
- Choisir le module initial après un test sur quelques contenus représentatifs.
