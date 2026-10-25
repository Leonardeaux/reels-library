"""Connexion initiale facultative : exporter uniquement les cookies Instagram.

Cette commande est exécutée volontairement sur une machine où le navigateur
est connecté, puis son fichier est transféré une fois vers le serveur.
"""

import argparse
import logging
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

from .domain import ValidationError
from .session import SessionStore


class CookieReadError(Exception):
    """Diagnostic utilisable sans afficher les sorties brutes du navigateur."""


class CookieDiagnostics(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.decryption_failed = False

    def emit(self, record):
        # Les messages peuvent contenir des informations privées : ne conserver
        # qu'un indicateur, jamais leur texte ni leurs arguments.
        if "decrypt" in record.getMessage().lower():
            self.decryption_failed = True


@contextmanager
def capture_cookie_diagnostics():
    logger = logging.getLogger("cookies")
    previous = (logger.handlers[:], logger.level, logger.propagate, logger.disabled)
    diagnostic = CookieDiagnostics()
    logger.handlers = [diagnostic]
    logger.setLevel(logging.WARNING)
    logger.propagate = False
    logger.disabled = False
    try:
        yield diagnostic
    finally:
        logger.handlers, level, logger.propagate, logger.disabled = previous
        logger.setLevel(level)
        diagnostic.close()


def decryption_message(browser):
    message = "[COOKIES_DECRYPTION_FAILED] Le connecteur ne peut pas déchiffrer les cookies."
    if browser == "chrome" and sys.platform == "win32":
        message += " Chrome sous Windows peut les protéger avec App-Bound Encryption, non pris en charge par ce connecteur."
    return message + " Pour préparer la session avec Firefox, connecte-toi à Instagram dans Firefox puis utilise --browser firefox."


def read_browser_cookies(browser, profile=None, loader=None):
    if loader is None:
        from gallery_dl.cookies import load_cookies
        loader = load_cookies
    with capture_cookie_diagnostics() as diagnostic:
        try:
            cookies = list(loader((browser, profile, None, None, ".instagram.com")))
        except FileNotFoundError:
            raise CookieReadError("[COOKIES_PROFILE_NOT_FOUND] Aucune base de cookies trouvée. Vérifie le navigateur installé et, si nécessaire, indique --profile avec le nom ou le chemin du profil connecté.") from None
        except (PermissionError, sqlite3.OperationalError) as error:
            if isinstance(error, PermissionError) or "locked" in str(error).lower() or getattr(error, "sqlite_errorcode", None) in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
                raise CookieReadError("[COOKIES_LOCKED] La base de cookies est verrouillée ou inaccessible. Ferme complètement le navigateur, puis relance la commande avec ton compte Windows habituel.") from None
            raise CookieReadError("[COOKIES_READ_FAILED] La base de cookies n'a pas pu être lue. Vérifie le profil choisi et l'installation du connecteur.") from None
        except Exception:
            if diagnostic.decryption_failed:
                raise CookieReadError(decryption_message(browser)) from None
            raise CookieReadError("[COOKIES_READ_FAILED] Lecture de session impossible. Vérifie la connexion Instagram et le profil choisi. Le détail brut n'est pas affiché car il peut contenir des informations privées.") from None
        if not any(cookie.name == "sessionid" and cookie.value for cookie in cookies):
            if diagnostic.decryption_failed:
                raise CookieReadError(decryption_message(browser))
            raise CookieReadError("[INSTAGRAM_SESSION_MISSING] Aucune session Instagram lisible dans ce profil. Connecte-toi à Instagram dans ce navigateur et indique --profile si plusieurs profils existent.")
        return cookies


def main():
    parser = argparse.ArgumentParser(description="Préparer une session Instagram pour le serveur")
    parser.add_argument("--browser", choices=("edge", "chrome", "firefox"), required=True)
    parser.add_argument("--profile", help="Nom du profil (par exemple Default ou Profile 1), ou chemin de son dossier")
    parser.add_argument("--output", type=Path, default=Path("sessions/instagram.cookies"))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.replace:
        parser.exit(1, "Le fichier existe déjà. Utilise --replace pour renouveler cette session.\n")
    try:
        cookies = read_browser_cookies(args.browser, args.profile)
        lines = ["# Netscape HTTP Cookie File"]
        for cookie in cookies:
            lines.append("\t".join((cookie.domain, "TRUE" if cookie.domain_initial_dot else "FALSE", cookie.path or "/", "TRUE" if cookie.secure else "FALSE", str(cookie.expires or 0), cookie.name, cookie.value or "")))
        SessionStore(args.output).install("\n".join(lines))
    except ImportError:
        parser.exit(1, "Installe le connecteur : python -m pip install -r requirements-sync.txt\n")
    except (ValidationError, CookieReadError) as error:
        parser.exit(1, str(error) + "\n")
    except OSError:
        parser.exit(1, "[SESSION_WRITE_FAILED] Le fichier de session n'a pas pu être écrit. Vérifie les permissions du dossier de sortie ou choisis un autre chemin avec --output.\n")
    except Exception:
        parser.exit(1, "Lecture de session impossible. Vérifie la connexion Instagram et l'accès aux cookies du navigateur.\n")
    print(f"Session créée : {args.output}. Transfère ce fichier dans la page Synchronisation du serveur.")


if __name__ == "__main__":
    main()
