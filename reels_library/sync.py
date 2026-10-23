"""Synchronisation expérimentale des sauvegardes sur un serveur autonome.

gallery-dl est exécuté dans un processus séparé, sans téléchargement de médias.
Les cookies et sorties brutes du connecteur ne sont ni journalisés ni conservés.
"""

import importlib.util
import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .domain import ValidationError, normalize_url, now
from .session import SessionStore

DEFAULT_SETTINGS = {"enabled": False, "interval_minutes": 60, "limit": 50}


class SyncError(Exception):
    pass


def validate_settings(data):
    if not isinstance(data, dict):
        raise ValidationError("Réglages de synchronisation invalides.")
    enabled = data.get("enabled", False)
    interval = data.get("interval_minutes", 60)
    limit = data.get("limit", 200)
    if not isinstance(enabled, bool):
        raise ValidationError("L'activation doit être un booléen.")
    if type(interval) is not int or interval not in {15, 60, 360, 1440}:
        raise ValidationError("Intervalle de synchronisation invalide.")
    if type(limit) is not int or limit not in {50, 200, 1000, 5000}:
        raise ValidationError("La limite doit être 50, 200, 1000 ou 5000 publications.")
    return {"enabled": enabled, "interval_minutes": interval, "limit": limit}


def connector_python():
    if importlib.util.find_spec("gallery_dl"):
        return sys.executable
    root = Path(__file__).resolve().parent.parent
    executable = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if executable.is_file():
        return str(executable)
    raise SyncError("Le connecteur n'est pas installé. Exécute les commandes d'installation du README.")


def connector_command(settings, session_path):
    return [connector_python(), "-m", "gallery_dl", "--config-ignore", "--no-input", "--no-colors",
            "--dump-json", "--no-download", "--retries", "1", "--http-timeout", "20", "--sleep-429", "60",
            "--cache-file", ":memory:", "--cookies", str(session_path),
            "-o", "extractor.instagram.max-posts=" + str(settings["limit"]),
            "-o", "extractor.cookies-update=false", "https://www.instagram.com/me/saved/"]


def parse_connector_output(output):
    try:
        messages = json.loads(output)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise SyncError("Le connecteur n'a pas renvoyé de résultat lisible. Vérifie la session Instagram et l'installation.") from error
    if not isinstance(messages, list):
        raise SyncError("Le format de réponse du connecteur a changé.")
    entries, seen = [], set()
    for message in messages:
        if not isinstance(message, list) or not message:
            raise SyncError("La réponse du connecteur est incomplète.")
        if message[0] == -1:
            # DataJob peut sortir avec le code 0 tout en contenant une erreur.
            detail = str(message[-1]).lower()
            if any(word in detail for word in ("429", "rate limit", "please wait")):
                raise SyncError("Instagram limite les requêtes. Réessaie plus tard ; la synchronisation automatique attendra avant de reprendre.")
            raise SyncError("Accès aux sauvegardes refusé ou interrompu. Renouvelle la session Instagram et vérifie les éventuelles demandes de vérification du compte.")
        if message[0] != 2:
            continue
        metadata = message[-1]
        if not isinstance(metadata, dict) or not metadata.get("post_url"):
            raise SyncError("Les références attendues sont absentes de la réponse du connecteur.")
        try:
            url, source_id = normalize_url(metadata["post_url"])
        except ValidationError as error:
            raise SyncError("Le connecteur a renvoyé un type de publication non pris en charge.") from error
        if source_id in seen:
            continue
        seen.add(source_id)
        # Liste explicite : ni cookies, ni URL de média, ni données du profil privé.
        caption = metadata.get("description") or ""
        author = metadata.get("username") or ""
        if not isinstance(caption, str) or not isinstance(author, str):
            raise SyncError("Le format des métadonnées du connecteur a changé.")
        entry = {"url": url, "title": caption.splitlines()[0][:160] if caption.strip() else "", "author": author[:120],
                 "caption": caption[:100000], "connector": "gallery-dl"}
        # Une date de publication n'est jamais présentée comme date de sauvegarde.
        if isinstance(metadata.get("post_date"), str):
            entry["published_at"] = metadata["post_date"]
        entries.append(entry)
    return entries


class SyncManager:
    def __init__(self, library, session_path=None):
        self.library = library
        self.session = SessionStore(session_path or library.path.parent / "instagram.cookies")
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.running = False
        self.process = None
        self.thread = None
        self.scheduler = None
        self.next_run = None
        self.failures = 0
        with self.library.connection() as connection:
            connection.execute("UPDATE sync_runs SET status='interrupted',finished_at=?,message=? WHERE status='running'", (now(), "Le serveur a été arrêté pendant la synchronisation. Une nouvelle tentative est possible."))

    def settings(self):
        stored = self.library.get_setting("sync", {})
        return {key: stored.get(key, value) for key, value in DEFAULT_SETTINGS.items()}

    def install_session(self, content):
        with self.lock:
            if self.running:
                raise ValidationError("Attends la fin du passage en cours pour remplacer la session.")
            return self.session.install(content)

    def clear_session(self):
        with self.lock:
            if self.running:
                raise ValidationError("Attends la fin du passage en cours pour retirer la session.")
            self.session.clear()
            settings = self.settings()
            settings["enabled"] = False
            self.library.set_setting("sync", settings)
            self.next_run = None

    def configure(self, data):
        settings = validate_settings(data)
        with self.lock:
            if self.running:
                raise ValidationError("Attends la fin du passage en cours avant de modifier la connexion.")
            if settings["enabled"] and not self.session.status()["configured"]:
                raise ValidationError("Fournis d'abord une session Instagram valide avant d'activer la synchronisation.")
            self.library.set_setting("sync", settings)
            self.next_run = datetime.now(timezone.utc) + timedelta(minutes=settings["interval_minutes"]) if settings["enabled"] else None
        return settings

    def status(self):
        with self.library.connection() as connection:
            runs = [dict(row) for row in connection.execute("SELECT s.*,i.total,i.imported,i.duplicate,i.ignored,i.error FROM sync_runs s LEFT JOIN imports i ON i.id=s.import_id ORDER BY s.started_at DESC,s.rowid DESC LIMIT 10")]
        with self.lock:
            return {"settings": self.settings(), "session": self.session.status(), "running": self.running,
                    "next_run": self.next_run.isoformat(timespec="seconds") if self.next_run else None, "runs": runs}

    def start_scheduler(self):
        if self.scheduler:
            return
        if self.settings()["enabled"]:
            self.next_run = datetime.now(timezone.utc)
        self.scheduler = threading.Thread(target=self._schedule, name="instagram-scheduler", daemon=True)
        self.scheduler.start()

    def _schedule(self):
        while not self.stop_event.wait(2):
            with self.lock:
                due = self.next_run and datetime.now(timezone.utc) >= self.next_run and not self.running
            if due:
                try:
                    self.start()
                except (ValidationError, SyncError) as error:
                    with self.library.connection() as connection:
                        timestamp = now()
                        connection.execute("INSERT INTO sync_runs(id,started_at,finished_at,status,message) VALUES(?,?,?,'error',?)", (uuid.uuid4().hex, timestamp, timestamp, str(error)))
                    with self.lock:
                        self.next_run = datetime.now(timezone.utc) + timedelta(minutes=60)

    def start(self):
        with self.lock:
            if self.stop_event.is_set():
                raise SyncError("Le serveur s'arrête.")
            if self.running:
                raise ValidationError("Une synchronisation est déjà en cours.")
            settings = validate_settings(self.settings())
            if not self.session.status()["configured"]:
                raise SyncError("La session Instagram est absente ou expirée. Fournis une session depuis la page Synchronisation.")
            command = connector_command(settings, self.session.path)
            identifier = uuid.uuid4().hex
            with self.library.connection() as connection:
                connection.execute("INSERT INTO sync_runs(id,started_at,status) VALUES(?,?,'running')", (identifier, now()))
            self.running = True
            self.next_run = None
            self.thread = threading.Thread(target=self._run, args=(identifier, settings, command), name="instagram-sync", daemon=True)
            self.thread.start()
            return {"id": identifier, "started": True}

    def _run(self, identifier, settings, command):
        status, message, import_id, limited = "error", "Le connecteur a rencontré une erreur. Vérifie la connexion Instagram.", None, False
        process = None
        try:
            with self.lock:
                if self.stop_event.is_set():
                    raise SyncError("La synchronisation a été arrêtée avec le serveur.")
                self.process = process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                        stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                output, _ = process.communicate(timeout=900)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise SyncError("Le passage a dépassé 15 minutes. Réduis la limite et réessaie ; les données déjà présentes sont conservées.") from None
            if process.returncode:
                raise SyncError("Le connecteur n'a pas pu lire les sauvegardes. Vérifie l'installation et renouvelle la session Instagram si nécessaire.")
            entries = parse_connector_output(output)
            if self.stop_event.is_set():
                raise SyncError("La synchronisation a été arrêtée avec le serveur.")
            report = self.library.import_content(json.dumps({"items": entries}, ensure_ascii=False), "Synchronisation Instagram")
            import_id = report["id"]
            limited = len(entries) >= settings["limit"]
            status = "success"
            message = f"{report['imported']} nouvelle(s) référence(s), {report['duplicate']} déjà présente(s)."
            if limited:
                message += " Limite atteinte : l'historique peut contenir d'autres sauvegardes."
        except SyncError as error:
            message = str(error)
        except Exception:
            # Ne jamais exposer les sorties du processus (elles peuvent contenir des secrets).
            message = "La synchronisation a échoué. Les fiches existantes sont conservées."
        finally:
            if process and process.poll() is None:
                process.kill()
                process.communicate()
            with self.library.connection() as connection:
                connection.execute("UPDATE sync_runs SET finished_at=?,status=?,message=?,import_id=?,limited=? WHERE id=?", (now(), status, message, import_id, limited, identifier))
            with self.lock:
                self.process = None
                self.running = False
                self.failures = 0 if status == "success" else self.failures + 1
                minutes = max(settings["interval_minutes"], min(1440, 60 * 2 ** min(self.failures, 5))) if self.failures else settings["interval_minutes"]
                self.next_run = datetime.now(timezone.utc) + timedelta(minutes=minutes) if settings["enabled"] and not self.stop_event.is_set() else None

    def close(self):
        self.stop_event.set()
        with self.lock:
            if self.process and self.process.poll() is None:
                self.process.terminate()
        if self.thread:
            self.thread.join(timeout=5)
        if self.scheduler:
            self.scheduler.join(timeout=3)
