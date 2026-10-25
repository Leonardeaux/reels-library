# Composants tiers

La [licence MIT](LICENSE) couvre le code de Reels Library. Les dépendances et images de base conservent leurs propres licences ; l'image Docker entière ne doit pas être présentée comme exclusivement sous MIT.

| Composant | Rôle | Licence et source |
| --- | --- | --- |
| Python | Exécution | [PSF et notices associées](https://docs.python.org/3/license.html) |
| Waitress 3.0.2 | Serveur WSGI | [ZPL-2.1, sources](https://github.com/Pylons/waitress/tree/v3.0.2) |
| gallery-dl 1.32.17 | Programme de récupération, lancé dans un processus séparé | GPL-2.0-only ; [sources et fichiers de cette version](https://pypi.org/project/gallery-dl/1.32.17/#files) |
| Caddy | Reverse proxy HTTPS facultatif | [Apache-2.0, sources](https://github.com/caddyserver/caddy) |

Les paquets installés dans le conteneur contiennent leurs notices dans `site-packages`, notamment la licence de gallery-dl dans son répertoire `.dist-info/licenses/`. Les dépendances transitives conservent également leurs notices.

La construction télécharge les dépendances depuis leurs distributions officielles ; ce dépôt ne redistribue pas d'exécutable desktop ni d'image préconstruite. Si tu distribues une image ou un autre paquet contenant ces composants, conserve leurs licences et fournis le code source correspondant lorsque leur licence l'exige. Pour récupérer la distribution source du connecteur :

```sh
python -m pip download --no-deps --no-binary=:all: gallery-dl==1.32.17
```
