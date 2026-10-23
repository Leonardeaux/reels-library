"""Validation des références et des informations personnelles."""

import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlsplit

STAGES = ("to_use", "in_progress", "used", "archived")
INTENTIONS = ("learn", "cook", "make", "reference")
KINDS = ("tutorial", "demo", "news", "opinion", "inspiration", "other")


class ValidationError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fold(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value)).casefold()
                   if not unicodedata.combining(c))


def normalize_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValidationError("Le lien doit être une URL Instagram valide.")
    value = value.strip()
    if re.search(r"\s", value):
        raise ValidationError("Le lien ne doit pas contenir d'espaces ou de retours à la ligne.")
    if value.startswith(("instagram.com/", "www.instagram.com/", "m.instagram.com/")):
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        valid_host = parsed.hostname in {"instagram.com", "www.instagram.com", "m.instagram.com"}
        valid_origin = parsed.scheme in {"http", "https"} and not parsed.username and not parsed.password and parsed.port is None
    except ValueError as error:
        raise ValidationError("Le lien Instagram est invalide.") from error
    if not valid_host or not valid_origin:
        raise ValidationError("Utilise un lien instagram.com vers un Reel ou une publication.")
    match = re.fullmatch(r"/(reel|reels|p)/([A-Za-z0-9_-]{1,80})/?", parsed.path)
    if not match:
        raise ValidationError("Ouvre la publication et copie son lien /reel/ ou /p/. Les liens de profil ou de partage court ne sont pas pris en charge.")
    route, code = match.groups()
    route = "reel" if route == "reels" else route
    return f"https://www.instagram.com/{route}/{code}/", f"instagram:{code}"


def text(value, field, maximum=2000):
    if not isinstance(value, str) or len(value) > maximum:
        raise ValidationError(f"{field} doit être un texte de {maximum} caractères maximum.")
    return value.strip()


def names(value, field):
    if not isinstance(value, list) or len(value) > 50:
        raise ValidationError(f"{field} doit contenir au plus 50 éléments.")
    result, seen = [], set()
    for item in value:
        item = text(item, field, 80)
        if item and fold(item) not in seen:
            result.append(item)
            seen.add(fold(item))
    return result


def saved_date(value):
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec="seconds")
        if not isinstance(value, str):
            raise ValueError()
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (ValueError, OverflowError, OSError) as error:
        raise ValidationError("La date de sauvegarde est invalide.") from error


def validate_personal(data):
    if not isinstance(data, dict):
        raise ValidationError("Une fiche doit être un objet JSON.")
    result = {}
    for key, limit in {"title": 240, "author": 120, "notes": 20000, "summary": 10000}.items():
        if key in data:
            result[key] = text(data[key], key, limit)
    for key, allowed in {"stage": STAGES, "intention": INTENTIONS, "kind": KINDS}.items():
        if key in data:
            if data[key] not in allowed:
                raise ValidationError(f"Valeur inconnue pour {key}.")
            result[key] = data[key]
    for key in ("tags", "categories", "collections"):
        if key in data:
            result[key] = names(data[key], key)
    if "starred" in data:
        if not isinstance(data["starred"], bool):
            raise ValidationError("La sélection doit être un booléen.")
        result["starred"] = data["starred"]
    return result
