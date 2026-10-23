"""Créer la clé de l'espace privé sans l'afficher ni écraser une clé existante."""

import os
import secrets
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent / "secrets"
    root.mkdir(mode=0o700, exist_ok=True)
    if os.name != "nt":
        root.chmod(0o700)
    target = root / "app_token"
    try:
        # Le répertoire 0700 protège le fichier sur l'hôte. Le conteneur non root
        # doit pouvoir lire ce fichier une fois monté par Compose dans /run/secrets.
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        print("Clé existante conservée : secrets/app_token")
        return
    if os.name != "nt":
        os.fchmod(descriptor, 0o644)
    with os.fdopen(descriptor, "w", encoding="ascii") as stream:
        stream.write(secrets.token_urlsafe(32) + "\n")
    print("Clé créée dans secrets/app_token. Identifiant de connexion : admin.")
    print("Ouvrez ce fichier pour copier la clé ; elle n'est pas affichée ici.")


if __name__ == "__main__":
    main()
