"""Clé privée d'une installation, créée une seule fois dans son volume Docker."""

import argparse
import os
import secrets
from pathlib import Path

from .domain import ValidationError


def read_key(path):
    value = Path(path).read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise ValidationError("La clé d'accès existante doit contenir au moins 32 caractères ; elle n'a pas été remplacée.")
    return value


def ensure_key(path):
    """Créer sans écraser une clé existante, sans en afficher la valeur."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return read_key(path)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as stream:
            stream.write(secrets.token_urlsafe(32) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return read_key(path)


def configured_key(environment):
    path = environment.get("REELS_ACCESS_TOKEN_FILE")
    create = environment.get("REELS_CREATE_ACCESS_TOKEN", "false").lower()
    if create not in {"true", "false", "1", "0"}:
        raise ValidationError("REELS_CREATE_ACCESS_TOKEN doit valoir true ou false.")
    if create in {"true", "1"}:
        if not path:
            raise ValidationError("REELS_ACCESS_TOKEN_FILE est nécessaire pour créer la clé d'accès.")
        return ensure_key(path)
    return read_key(path) if path else environment.get("REELS_ACCESS_TOKEN")


def main():
    parser = argparse.ArgumentParser(description="Afficher volontairement la clé privée de cette installation (identifiant : admin).")
    parser.add_argument("--file", type=Path, default=Path(os.environ.get("REELS_ACCESS_TOKEN_FILE", "/app/config/app_token")))
    args = parser.parse_args()
    try:
        value = read_key(args.file)
    except (OSError, UnicodeError, ValidationError) as error:
        parser.exit(1, f"Lecture de la clé impossible : {error}\n")
    print(value)


if __name__ == "__main__":
    main()
