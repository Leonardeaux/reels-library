"""Lecture ciblée des sauvegardes : chaque entrée reste comptabilisée."""

import json
from dataclasses import dataclass, field

from .domain import ValidationError, normalize_url, saved_date, text, validate_personal

MAX_ENTRIES = 50000


@dataclass
class Candidate:
    position: int
    url: str = ""
    source_id: str = ""
    title: str = ""
    author: str = ""
    saved_at: str | None = None
    imported_at: str | None = None
    updated_at: str | None = None
    source_text: str = ""
    collections: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    personal: dict = field(default_factory=dict)
    sources: list = field(default_factory=list)
    problem: str = ""
    problem_status: str = "ignored"


def _extract(entry, position, backup=False):
    candidate = Candidate(position)
    if not isinstance(entry, dict):
        candidate.problem = "L'entrée n'est pas un objet JSON."
        candidate.problem_status = "error"
        return candidate
    # On ne conserve que l'entrée de sauvegarde, jamais l'export de compte entier.
    candidate.raw = entry if not backup else {}
    try:
        url = entry.get("url") or entry.get("href") or ""
        timestamp = entry.get("saved_at")
        mapping = entry.get("string_map_data", {})
        if isinstance(mapping, dict):
            for value in mapping.values():
                if isinstance(value, dict) and value.get("href"):
                    url = url or value["href"]
                    timestamp = timestamp if timestamp is not None else value.get("timestamp")
                    break
        string_data = entry.get("string_list_data", [])
        if isinstance(string_data, list):
            for value in string_data:
                if isinstance(value, dict) and value.get("href"):
                    url = url or value["href"]
                    timestamp = timestamp if timestamp is not None else value.get("timestamp")
                    break
        candidate.url, candidate.source_id = normalize_url(url)
        candidate.saved_at = saved_date(timestamp)
        candidate.title = text(entry.get("title") or "", "Titre", 240)
        candidate.author = text(entry.get("author") or "", "Auteur", 120)
        candidate.source_text = text(entry.get("source_text") or entry.get("caption") or "", "Texte source", 100000)
        candidate.collections = validate_personal({"collections": entry.get("collections", [])})["collections"]
        if backup:
            candidate.imported_at = saved_date(entry.get("imported_at"))
            candidate.updated_at = saved_date(entry.get("updated_at"))
            candidate.personal = validate_personal(entry)
            sources = entry.get("sources", [])
            if not isinstance(sources, list) or len(sources) > 100:
                raise ValidationError("La liste des sources est invalide.")
            for source in sources:
                if not isinstance(source, dict) or source.get("kind") not in {"manual", "import"}:
                    raise ValidationError("Une source de la sauvegarde est invalide.")
                candidate.sources.append({"kind": source["kind"], "text": text(source.get("text", ""), "Texte source", 100000), "raw": source.get("raw", {}), "created_at": saved_date(source.get("created_at"))})
    except ValidationError as error:
        candidate.problem = str(error)
        candidate.problem_status = "ignored" if not candidate.url else "error"
    return candidate


def parse_import(content, filename="import.json"):
    if not isinstance(content, str) or not content.strip():
        raise ValidationError("Le fichier est vide.")
    stripped = content.lstrip("\ufeff \r\n\t")
    if filename.lower().endswith(".json") or stripped.startswith(("{", "[")):
        try:
            payload = json.loads(stripped)
        except (ValueError, RecursionError) as error:
            raise ValidationError("Le fichier JSON est invalide. Choisis le fichier des sauvegardes, pas une archive ZIP.") from error
        backup = isinstance(payload, dict) and payload.get("format") == "reels-library"
        if backup:
            if payload.get("version") != 1:
                raise ValidationError("Version de sauvegarde non prise en charge.")
            entries = payload.get("reels")
        elif isinstance(payload, list):
            entries = payload
        elif isinstance(payload, dict):
            entries = next((payload[key] for key in ("saved_saved_media", "saved_media", "saved_posts", "items") if key in payload), None)
        else:
            entries = None
        if not isinstance(entries, list):
            raise ValidationError("Format inconnu. Utilise un JSON de sauvegardes (saved_saved_media, saved_media, saved_posts ou items), une liste d'objets, ou un fichier texte avec un lien par ligne.")
        if len(entries) > MAX_ENTRIES:
            raise ValidationError(f"Import limité à {MAX_ENTRIES} entrées par fichier.")
        return [_extract(entry, index + 1, backup) for index, entry in enumerate(entries)]
    if filename.lower().endswith((".html", ".htm", ".zip")) or stripped.startswith("<"):
        raise ValidationError("Ce format n'est pas encore pris en charge. Utilise le JSON des sauvegardes ou un fichier texte, un lien par ligne.")
    lines = [(index + 1, line.strip()) for index, line in enumerate(content.splitlines()) if line.strip() and not line.lstrip().startswith("#")]
    if len(lines) > MAX_ENTRIES:
        raise ValidationError(f"Import limité à {MAX_ENTRIES} entrées par fichier.")
    return [_extract({"url": line}, index) for index, line in lines]
