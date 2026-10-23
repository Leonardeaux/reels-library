"""Session Instagram conservée hors base, exports et code applicatif."""

import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .domain import ValidationError


def clean_cookies(content):
    if not isinstance(content, str) or len(content.encode("utf-8")) > 128 * 1024:
        raise ValidationError("Le fichier de session doit être un texte Netscape de 128 Ko maximum.")
    result = ["# Netscape HTTP Cookie File", "# Session Instagram de Reels Library"]
    authenticated = False
    for position, line in enumerate(content.lstrip("\ufeff").splitlines(), 1):
        if not line.strip() or (line.startswith("#") and not line.startswith("#HttpOnly_")):
            continue
        fields = line.split("\t")
        if len(fields) != 7:
            raise ValidationError(f"Format de session invalide à la ligne {position}. Un fichier Netscape cookies.txt est attendu.")
        domain, subdomains, path, secure, expires, name, value = fields
        hostname = domain.removeprefix("#HttpOnly_").lstrip(".").lower()
        if hostname != "instagram.com" and not hostname.endswith(".instagram.com"):
            continue
        if subdomains not in {"TRUE", "FALSE"} or secure not in {"TRUE", "FALSE"} or not path.startswith("/"):
            raise ValidationError(f"Attributs de session invalides à la ligne {position}.")
        try:
            expiration = int(expires)
        except ValueError as error:
            raise ValidationError(f"Expiration de session invalide à la ligne {position}.") from error
        if expiration < 0 or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name) or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValidationError(f"Cookie invalide à la ligne {position}.")
        if expiration and expiration <= time.time():
            continue
        if name == "sessionid" and value:
            authenticated = True
        result.append("\t".join(fields))
    if not authenticated:
        raise ValidationError("Aucune session Instagram valide dans ce fichier. Connecte-toi au compte et fournis une nouvelle session.")
    return "\n".join(result) + "\n"


class SessionStore:
    def __init__(self, path):
        self.path = Path(path)

    def status(self):
        try:
            clean_cookies(self.path.read_text(encoding="utf-8"))
            timestamp = datetime.fromtimestamp(self.path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
            return {"configured": True, "updated_at": timestamp}
        except (OSError, UnicodeError, ValidationError):
            return {"configured": False, "updated_at": None}

    def install(self, content):
        cleaned = clean_cookies(content)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.path.with_name(".session-" + uuid.uuid4().hex)
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(cleaned)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return self.status()

    def clear(self):
        self.path.unlink(missing_ok=True)
