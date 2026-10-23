"""Connexion initiale facultative : exporter uniquement les cookies Instagram.

Cette commande est exécutée volontairement sur une machine où le navigateur
est connecté, puis son fichier est transféré une fois vers le serveur.
"""

import argparse
import logging
from pathlib import Path

from .domain import ValidationError
from .session import SessionStore


def main():
    parser = argparse.ArgumentParser(description="Préparer une session Instagram pour le serveur")
    parser.add_argument("--browser", choices=("edge", "chrome", "firefox"), required=True)
    parser.add_argument("--output", type=Path, default=Path("sessions/instagram.cookies"))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.replace:
        parser.exit(1, "Le fichier existe déjà. Utilise --replace pour renouveler cette session.\n")
    try:
        from gallery_dl.cookies import load_cookies
    except ImportError:
        parser.exit(1, "Installe le connecteur : python -m pip install -r requirements-sync.txt\n")
    logging.disable(logging.CRITICAL)
    try:
        cookies = load_cookies((args.browser, None, None, None, ".instagram.com"))
        lines = ["# Netscape HTTP Cookie File"]
        for cookie in cookies:
            lines.append("\t".join((cookie.domain, "TRUE" if cookie.domain_initial_dot else "FALSE", cookie.path or "/", "TRUE" if cookie.secure else "FALSE", str(cookie.expires or 0), cookie.name, cookie.value or "")))
        SessionStore(args.output).install("\n".join(lines))
    except ValidationError as error:
        parser.exit(1, str(error) + "\n")
    except Exception:
        parser.exit(1, "Lecture de session impossible. Vérifie la connexion Instagram et l'accès aux cookies du navigateur.\n")
    print(f"Session créée : {args.output}. Transfère ce fichier dans la page Synchronisation du serveur.")


if __name__ == "__main__":
    main()
