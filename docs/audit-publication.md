# Vérifications avant publication

Audit effectué le 25 octobre 2026, avant la première ouverture publique.

## Périmètre

- Fichiers suivis et toutes leurs versions accessibles dans l'historique, branches et tags.
- Métadonnées et messages des commits.
- Comparaison en mémoire avec les valeurs des cookies et de la clé présents localement, sans afficher ni publier ces valeurs.
- Exclusion des fichiers personnels par Git et du contexte de construction Docker.
- Éléments associés au dépôt GitHub : références, issues, releases, artefacts et journaux d'exécution.

Gitleaks 8.30.1 a examiné l'historique, une extraction des fichiers suivis et les journaux GitHub Actions. Des contrôles complémentaires ont recherché les clés privées, les chemins personnels, les adresses e-mail, les cookies et les URL contenant des identifiants. Les seuls identifiants trouvés dans le code étaient des exemples fictifs de tests de validation.

## Résultat et corrections

Aucun secret réel n'a été détecté dans le code ou ses versions historiques. Les cookies et la clé locale sont ignorés par Git et leurs valeurs n'ont pas été retrouvées dans les objets examinés. Aucun export personnel, base locale ou média n'était suivi.

Les métadonnées historiques contenaient des coordonnées non masquées. Elles ont été remplacées par le pseudonyme public et l'adresse GitHub « noreply ». Le code et les étapes de développement sont conservés. Une nouvelle copie du dépôt est utilisée pour la publication ; l'original reste privé afin de ne pas exposer ses anciens objets Git ou leurs vues en cache.

Les prochains commits de ce poste utilisent également l'identité publique. La CI inclut un contrôle de secrets sur l'historique complet, sans afficher les valeurs détectées. Les fichiers personnels restent sur le poste de l'utilisateur, hors distribution.

Ces vérifications décrivent ce qui a été recherché et corrigé à cette date ; elles ne garantissent pas l'absence de toute information sensible ni la sécurité de futures modifications.
