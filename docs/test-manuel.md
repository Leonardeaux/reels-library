# Test manuel de la bibliothèque

[Retour au README](../README.md)

Commence par lancer le conteneur et te connecter depuis le README.

## Tester la bibliothèque sans Instagram

### Premier import

1. Clique sur **Importer**.
2. Choisis le fichier [examples/instagram-demo.json](../examples/instagram-demo.json) présent dans le dépôt.
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
