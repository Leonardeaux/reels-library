"""Persistance relationnelle et opérations transactionnelles de bibliothèque."""

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from .domain import ValidationError, fold, names, normalize_url, now, saved_date, text, validate_personal
from .importers import Candidate, parse_import

SCHEMA = """
CREATE TABLE IF NOT EXISTS reels (
    id TEXT PRIMARY KEY, source_id TEXT NOT NULL UNIQUE, url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '', author TEXT NOT NULL DEFAULT '',
    saved_at TEXT, imported_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL DEFAULT 'to_use', intention TEXT NOT NULL DEFAULT 'reference',
    kind TEXT NOT NULL DEFAULT 'other', starred INTEGER NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY, reel_id TEXT NOT NULL REFERENCES reels(id) ON DELETE CASCADE,
    kind TEXT NOT NULL, text TEXT NOT NULL DEFAULT '', raw TEXT NOT NULL DEFAULT '{}',
    fingerprint TEXT NOT NULL, created_at TEXT NOT NULL,
    UNIQUE(reel_id, fingerprint)
);
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE,
    archived INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reel_categories (
    reel_id TEXT NOT NULL REFERENCES reels(id) ON DELETE CASCADE,
    category_id TEXT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY(reel_id, category_id)
);
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS reel_collections (
    reel_id TEXT NOT NULL REFERENCES reels(id) ON DELETE CASCADE,
    collection_id TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY(reel_id, collection_id)
);
CREATE TABLE IF NOT EXISTS imports (
    id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT NOT NULL,
    total INTEGER NOT NULL, imported INTEGER NOT NULL, duplicate INTEGER NOT NULL,
    ignored INTEGER NOT NULL, error INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS import_entries (
    id INTEGER PRIMARY KEY, import_id TEXT NOT NULL REFERENCES imports(id) ON DELETE CASCADE,
    position INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL,
    reel_id TEXT REFERENCES reels(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sync_runs (
    id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
    status TEXT NOT NULL, message TEXT NOT NULL DEFAULT '',
    import_id TEXT REFERENCES imports(id), limited INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS sources_reel ON sources(reel_id);
PRAGMA user_version = 2;
"""


class Library:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise RuntimeError("Cette base nécessite une version plus récente de Reels Library.")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(SCHEMA)
            if version == 0:
                for name in ("Cuisine", "Informatique & IA", "Making & DIY"):
                    self._taxonomy_id(connection, "categories", name)

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _taxonomy_id(self, connection, table, name):
        # table est exclusivement une constante interne.
        key = fold(name)
        row = connection.execute(f"SELECT id FROM {table} WHERE name_key=?", (key,)).fetchone()
        if row:
            return row["id"]
        identifier = uuid.uuid4().hex
        connection.execute(f"INSERT INTO {table}(id,name,name_key) VALUES(?,?,?)", (identifier, name, key))
        return identifier

    def _assign(self, connection, reel_id, table, values):
        relation = "reel_categories" if table == "categories" else "reel_collections"
        column = "category_id" if table == "categories" else "collection_id"
        connection.execute(f"DELETE FROM {relation} WHERE reel_id=?", (reel_id,))
        for name in values:
            identifier = self._taxonomy_id(connection, table, name)
            connection.execute(f"INSERT INTO {relation}(reel_id,{column}) VALUES(?,?)", (reel_id, identifier))

    def _source(self, connection, reel_id, kind, source_text, raw, created_at=None):
        raw_json = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        fingerprint = hashlib.sha256((kind + "\n" + source_text + "\n" + raw_json).encode()).hexdigest()
        if kind == "manual":
            latest = connection.execute("SELECT text FROM sources WHERE reel_id=? AND kind='manual' ORDER BY id DESC LIMIT 1", (reel_id,)).fetchone()
            if latest and latest["text"] == source_text:
                return
            fingerprint = uuid.uuid4().hex
        connection.execute("INSERT OR IGNORE INTO sources(reel_id,kind,text,raw,fingerprint,created_at) VALUES(?,?,?,?,?,?)",
                           (reel_id, kind, source_text, raw_json, fingerprint, created_at or now()))

    def _insert(self, connection, candidate):
        identifier = uuid.uuid4().hex
        timestamp = now()
        connection.execute("INSERT INTO reels(id,source_id,url,title,author,saved_at,imported_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                           (identifier, candidate.source_id, candidate.url, candidate.title, candidate.author,
                            candidate.saved_at, candidate.imported_at or timestamp, candidate.updated_at or timestamp))
        self._assign(connection, identifier, "collections", candidate.collections)
        if candidate.sources:
            for source in candidate.sources:
                self._source(connection, identifier, source["kind"], source["text"], source["raw"], source["created_at"])
        else:
            self._source(connection, identifier, "import", candidate.source_text, candidate.raw)
        if candidate.personal:
            self._update(connection, identifier, candidate.personal)
            if candidate.updated_at:
                connection.execute("UPDATE reels SET updated_at=? WHERE id=?", (candidate.updated_at, identifier))
        return identifier

    def _all(self, connection):
        reels = [dict(row) for row in connection.execute("SELECT * FROM reels ORDER BY imported_at DESC, rowid DESC")]
        by_id = {reel["id"]: reel for reel in reels}
        for reel in reels:
            reel["tags"] = json.loads(reel["tags"])
            reel["starred"] = bool(reel["starred"])
            reel["categories"], reel["collections"], reel["sources"] = [], [], []
        for table, relation, column in (("categories", "reel_categories", "category_id"), ("collections", "reel_collections", "collection_id")):
            for row in connection.execute(f"SELECT rel.reel_id, t.name FROM {relation} rel JOIN {table} t ON t.id=rel.{column} ORDER BY t.name_key"):
                by_id[row["reel_id"]][table].append(row["name"])
        for row in connection.execute("SELECT * FROM sources ORDER BY id"):
            source = dict(row)
            source["raw"] = json.loads(source["raw"])
            by_id[source["reel_id"]]["sources"].append(source)
        for reel in reels:
            manual = [source for source in reel["sources"] if source["kind"] == "manual"]
            imported = [source for source in reel["sources"] if source["text"]]
            preferred = (manual or imported or reel["sources"])
            current = preferred[-1] if preferred else None
            reel["source_text"] = current["text"] if current else ""
            reel["source_kind"] = current["kind"] if current else "import"
            reel["technical_status"] = "text_available" if reel["source_text"] else "reference_only"
            reel["search_text"] = fold(" ".join([reel["title"], reel["author"], reel["notes"], reel["summary"], reel["source_text"], reel["url"], *reel["tags"], *reel["categories"], *reel["collections"]]))
        return reels

    def get(self, identifier):
        with self.connection() as connection:
            return next((item for item in self._all(connection) if item["id"] == identifier), None)

    def list(self, filters=None):
        filters = filters or {}
        with self.connection() as connection:
            reels = self._all(connection)
            categories = [dict(row) for row in connection.execute("SELECT c.*,COUNT(rc.reel_id) AS count FROM categories c LEFT JOIN reel_categories rc ON rc.category_id=c.id GROUP BY c.id ORDER BY c.name_key")]
            collections = [dict(row) for row in connection.execute("SELECT c.*,COUNT(rc.reel_id) AS count FROM collections c LEFT JOIN reel_collections rc ON rc.collection_id=c.id GROUP BY c.id ORDER BY c.name_key")]
        stats = {"total": len(reels), "to_use": sum(item["stage"] == "to_use" for item in reels),
                 "used": sum(item["stage"] == "used" for item in reels),
                 "starred": sum(item["starred"] for item in reels),
                 "unclassified": sum(not item["categories"] for item in reels),
                 "text_available": sum(bool(item["source_text"]) for item in reels)}
        terms = fold(filters.get("q", "")).split()
        result = []
        for reel in reels:
            if any(term not in reel["search_text"] for term in terms):
                continue
            if any(filters.get(key) and filters[key] != reel[key] for key in ("stage", "intention", "technical_status")):
                continue
            if filters.get("category") == "__unclassified__" and reel["categories"]:
                continue
            if filters.get("category") and filters["category"] != "__unclassified__" and filters["category"] not in reel["categories"]:
                continue
            if filters.get("collection") and filters["collection"] not in reel["collections"]:
                continue
            if filters.get("starred") == "1" and not reel["starred"]:
                continue
            result.append({key: value for key, value in reel.items() if key not in {"sources", "search_text"}})
        if filters.get("sort") == "title":
            result.sort(key=lambda reel: fold(reel["title"] or reel["source_id"]))
        elif filters.get("sort") == "saved":
            result.sort(key=lambda reel: reel["saved_at"] or "", reverse=True)
        return {"reels": result, "stats": stats, "categories": categories, "collections": collections}

    def create(self, data):
        personal = validate_personal(data)
        url, source_id = normalize_url(data.get("url", ""))
        source_text = text(data.get("source_text", ""), "Texte source", 100000)
        candidate = Candidate(1, url=url, source_id=source_id, saved_at=saved_date(data.get("saved_at")))
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT id FROM reels WHERE source_id=?", (source_id,)).fetchone()
            if existing:
                return {"id": existing["id"], "duplicate": True}
            identifier = self._insert(connection, candidate)
            self._update(connection, identifier, personal)
            if source_text:
                self._source(connection, identifier, "manual", source_text, {})
        return {"id": identifier, "duplicate": False}

    def _update(self, connection, identifier, personal):
        for key, value in personal.items():
            if key in {"categories", "collections"}:
                self._assign(connection, identifier, key, value)
            else:
                if key == "tags":
                    value = json.dumps(value, ensure_ascii=False)
                connection.execute(f"UPDATE reels SET {key}=? WHERE id=?", (value, identifier))
        connection.execute("UPDATE reels SET updated_at=? WHERE id=?", (now(), identifier))

    def update(self, identifier, data):
        personal = validate_personal(data)
        source_text = text(data["source_text"], "Texte source", 100000) if "source_text" in data else None
        with self.connection() as connection:
            if not connection.execute("SELECT 1 FROM reels WHERE id=?", (identifier,)).fetchone():
                return False
            self._update(connection, identifier, personal)
            if source_text is not None:
                self._source(connection, identifier, "manual", source_text, {})
        return True

    def delete(self, identifier):
        with self.connection() as connection:
            return connection.execute("DELETE FROM reels WHERE id=?", (identifier,)).rowcount > 0

    def category(self, data, identifier=None):
        if not isinstance(data, dict):
            raise ValidationError("Catégorie invalide.")
        name = text(data.get("name", ""), "Nom de catégorie", 80)
        if not name:
            raise ValidationError("Le nom de la catégorie est obligatoire.")
        archived = data.get("archived", False)
        if not isinstance(archived, bool):
            raise ValidationError("État d'archivage invalide.")
        with self.connection() as connection:
            if identifier:
                if not connection.execute("SELECT 1 FROM categories WHERE id=?", (identifier,)).fetchone():
                    return None
                duplicate = connection.execute("SELECT id FROM categories WHERE name_key=? AND id<>?", (fold(name), identifier)).fetchone()
                if duplicate:
                    raise ValidationError("Une catégorie de ce nom existe déjà.")
                connection.execute("UPDATE categories SET name=?,name_key=?,archived=? WHERE id=?", (name, fold(name), archived, identifier))
            else:
                identifier = self._taxonomy_id(connection, "categories", name)
            return {"id": identifier, "name": name, "archived": archived}

    def import_content(self, content, filename, preview=False):
        filename = text(filename, "Nom de fichier", 240)
        candidates = parse_import(content, filename)
        report = {"id": None, "filename": filename, "total": len(candidates), "imported": 0, "duplicate": 0, "ignored": 0, "error": 0, "entries": []}
        with self.connection() as connection:
            if not preview:
                connection.execute("BEGIN IMMEDIATE")
            existing = {row["source_id"]: row["id"] for row in connection.execute("SELECT id,source_id FROM reels")}
            for candidate in candidates:
                status, reason, identifier = "imported", "Nouvelle référence", None
                if candidate.problem:
                    status, reason = candidate.problem_status, candidate.problem
                elif candidate.source_id in existing:
                    status, reason, identifier = "duplicate", "Référence déjà présente ; corrections conservées", existing[candidate.source_id]
                    if not preview and candidate.raw:
                        self._source(connection, identifier, "import", candidate.source_text, candidate.raw)
                else:
                    if not preview:
                        identifier = self._insert(connection, candidate)
                    existing[candidate.source_id] = identifier
                report[status] += 1
                report["entries"].append({"position": candidate.position, "status": status, "reason": reason, "url": candidate.url, "title": candidate.title, "reel_id": identifier})
            if not preview:
                report["id"] = uuid.uuid4().hex
                connection.execute("INSERT INTO imports VALUES(?,?,?,?,?,?,?,?)", (report["id"], filename, now(), report["total"], report["imported"], report["duplicate"], report["ignored"], report["error"]))
                connection.executemany("INSERT INTO import_entries(import_id,position,status,reason,reel_id) VALUES(?,?,?,?,?)", [(report["id"], entry["position"], entry["status"], entry["reason"], entry["reel_id"]) for entry in report["entries"]])
        return report

    def import_history(self):
        with self.connection() as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM imports ORDER BY created_at DESC,rowid DESC LIMIT 20")]

    def get_setting(self, key, default=None):
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return json.loads(row["value"]) if row else default

    def set_setting(self, key, value):
        with self.connection() as connection:
            connection.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))

    def export(self):
        with self.connection() as connection:
            reels = self._all(connection)
        for reel in reels:
            for key in ("id", "source_id", "search_text", "source_kind", "technical_status"):
                reel.pop(key, None)
            for source in reel["sources"]:
                for key in ("id", "reel_id", "fingerprint"):
                    source.pop(key, None)
        return {"format": "reels-library", "version": 1, "exported_at": now(), "reels": reels}
