"""Serveur WSGI, configuré par REELS_* ou les arguments de lancement."""

import argparse
import os
import signal
from pathlib import Path

from .domain import ValidationError
from .web import Application


def main():
    parser = argparse.ArgumentParser(description="Reels Library — bibliothèque personnelle")
    parser.add_argument("--host", default=os.environ.get("REELS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("REELS_PORT", "8765")))
    parser.add_argument("--database", type=Path, default=Path(os.environ.get("REELS_DATABASE", "data/library.sqlite3")))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Le port doit être compris entre 1 et 65535.")
    try:
        from waitress import serve
    except ImportError:
        parser.exit(1, "Installe les dépendances : python -m pip install -r requirements.txt -r requirements-sync.txt\n")
    token_file = os.environ.get("REELS_ACCESS_TOKEN_FILE")
    try:
        token = Path(token_file).read_text(encoding="utf-8").strip() if token_file else os.environ.get("REELS_ACCESS_TOKEN")
        if args.host not in {"127.0.0.1", "localhost", "::1"} and not token:
            raise ValidationError("Une clé d'accès est obligatoire pour écouter en dehors de la boucle locale.")
        public_url = os.environ.get("REELS_PUBLIC_URL", f"http://127.0.0.1:{args.port}")
        app = Application(args.database, public_url, token, os.environ.get("REELS_SESSION_FILE", "sessions/instagram.cookies"))
    except (OSError, ValidationError) as error:
        parser.exit(1, f"Configuration impossible : {error}\n")
    print(f"Reels Library : {app.public_url}", flush=True)
    print("Synchronisation exécutée par le serveur ; aucune fenêtre de navigateur nécessaire.", flush=True)

    def stop(signum, frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, stop)
    app.sync.start_scheduler()
    try:
        serve(app, host=args.host, port=args.port, threads=8, max_request_body_size=20 * 1024 * 1024,
              channel_timeout=30, expose_tracebacks=False, clear_untrusted_proxy_headers=True)
    except KeyboardInterrupt:
        pass
    finally:
        app.close()


if __name__ == "__main__":
    main()
