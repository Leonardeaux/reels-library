"""Application WSGI personnelle, utilisable derrière un reverse proxy HTTPS."""

import base64
import binascii
import hmac
import json
import logging
import re
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .database import Library
from .domain import ValidationError
from .sync import SyncError, SyncManager

MAX_BODY = 20 * 1024 * 1024
STATIC = Path(__file__).with_name("static")
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/styles.css": ("styles.css", "text/css; charset=utf-8"),
          "/favicon.svg": ("favicon.svg", "image/svg+xml")}


class RequestError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def validate_public_url(value):
    try:
        parsed = urlsplit(value)
        parsed.port
    except (ValueError, TypeError) as error:
        raise ValidationError("REELS_PUBLIC_URL doit être une URL valide.") from error
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValidationError("REELS_PUBLIC_URL doit être une origine sans chemin, par exemple https://reels.exemple.fr.")
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not loopback:
        raise ValidationError("Une adresse publique nécessite HTTPS. Configure le reverse proxy et REELS_PUBLIC_URL.")
    return f"{parsed.scheme}://{parsed.netloc.lower()}", loopback


class Application:
    def __init__(self, database_path, public_url="http://127.0.0.1:8765", access_token=None, session_path=None):
        self.public_url, loopback = validate_public_url(public_url)
        if access_token is not None and len(access_token) < 32:
            raise ValidationError("La clé d'accès doit contenir au moins 32 caractères.")
        if not loopback and not access_token:
            raise ValidationError("Une clé d'accès est obligatoire pour un déploiement distant.")
        self.access_token = access_token
        self.library = Library(database_path)
        self.sync = SyncManager(self.library, session_path)

    def _check_request(self, environ):
        parsed = urlsplit(self.public_url)
        allowed_hosts, allowed_origins = {parsed.netloc}, {self.public_url}
        if parsed.hostname in {"127.0.0.1", "localhost"}:
            suffix = f":{parsed.port}" if parsed.port else ""
            for hostname in ("127.0.0.1", "localhost"):
                allowed_hosts.add(hostname + suffix)
                allowed_origins.add(parsed.scheme + "://" + hostname + suffix)
        if environ.get("HTTP_HOST", "").lower() not in allowed_hosts:
            raise RequestError(403, "Hôte non autorisé. Utilise l'adresse configurée pour cette bibliothèque.")
        origin = environ.get("HTTP_ORIGIN")
        if origin is not None and origin not in allowed_origins:
            raise RequestError(403, "Cette origine n'est pas autorisée.")
        if environ.get("HTTP_SEC_FETCH_SITE") == "cross-site" and environ.get("PATH_INFO", "").startswith("/api/"):
            raise RequestError(403, "Requête intersite refusée.")
        if self.access_token:
            authorization = environ.get("HTTP_AUTHORIZATION", "")
            supplied = ""
            if authorization.startswith("Basic "):
                try:
                    credentials = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
                    username, password = credentials.split(":", 1)
                    if username == "admin":
                        supplied = password
                except (ValueError, UnicodeError, binascii.Error):
                    pass
            elif authorization.startswith("Bearer "):
                supplied = authorization[7:]
            if not hmac.compare_digest(supplied.encode("utf-8"), self.access_token.encode("utf-8")):
                raise RequestError(401, "Connexion requise. Utilise l'identifiant admin et la clé d'accès de cette bibliothèque.")
        if environ["REQUEST_METHOD"] in {"POST", "PATCH"} and environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
            raise RequestError(415, "Une requête JSON est attendue.")

    def _body(self, environ):
        try:
            size = int(environ.get("CONTENT_LENGTH") or "0")
        except ValueError as error:
            raise RequestError(400, "Taille de requête invalide.") from error
        if size <= 0 or size > MAX_BODY:
            raise RequestError(413, "La requête doit contenir entre 1 octet et 20 Mo de JSON.")
        try:
            payload = json.loads(environ["wsgi.input"].read(size).decode("utf-8"))
        except (ValueError, UnicodeError, RecursionError) as error:
            raise RequestError(400, "Le contenu JSON est invalide.") from error
        if not isinstance(payload, dict):
            raise RequestError(400, "Un objet JSON est attendu.")
        return payload

    def _response(self, status, body, content_type="application/json; charset=utf-8", download=False):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = [("Content-Type", content_type), ("Content-Length", str(len(body))), ("Cache-Control", "no-store"),
                   ("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "no-referrer"),
                   ("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")]
        if status == 401:
            headers.append(("WWW-Authenticate", 'Basic realm="Reels Library", charset="UTF-8"'))
        if self.public_url.startswith("https:"):
            headers.append(("Strict-Transport-Security", "max-age=31536000"))
        if download:
            headers.append(("Content-Disposition", 'attachment; filename="reels-library.json"'))
        return status, headers, body

    def _dispatch(self, environ):
        method, path = environ["REQUEST_METHOD"], environ.get("PATH_INFO", "/")
        if method == "GET" and path == "/api/health":
            return self._response(200, {"status": "ok", "version": __version__})
        self._check_request(environ)
        library = self.library
        if method == "GET":
            if path in ASSETS:
                filename, content_type = ASSETS[path]
                return self._response(200, (STATIC / filename).read_bytes(), content_type)
            if path == "/api/library":
                filters = {key: values[0] for key, values in parse_qs(environ.get("QUERY_STRING", "")).items()}
                return self._response(200, library.list(filters))
            if path == "/api/export":
                return self._response(200, library.export(), download=True)
            if path == "/api/imports":
                return self._response(200, {"imports": library.import_history()})
            if path == "/api/sync":
                return self._response(200, self.sync.status())
            if re.fullmatch(r"/api/reels/[a-f0-9]{32}", path):
                reel = library.get(path.rsplit("/", 1)[1])
                if reel:
                    reel.pop("search_text", None)
                    return self._response(200, reel)
        elif method == "POST":
            data = self._body(environ)
            if path == "/api/reels":
                result = library.create(data)
                return self._response(200 if result["duplicate"] else 201, result)
            if path in {"/api/import/preview", "/api/import"}:
                return self._response(200, library.import_content(data.get("content"), data.get("filename", "import.json"), path.endswith("/preview")))
            if path == "/api/categories":
                return self._response(201, library.category(data))
            if path == "/api/sync/settings":
                return self._response(200, self.sync.configure(data))
            if path == "/api/sync/session":
                return self._response(200, self.sync.install_session(data.get("content")))
            if path == "/api/sync/start":
                return self._response(202, self.sync.start())
        elif method == "PATCH":
            data = self._body(environ)
            identifier = path.rsplit("/", 1)[-1]
            if re.fullmatch(r"/api/reels/[a-f0-9]{32}", path) and library.update(identifier, data):
                return self._response(200, {"updated": True})
            if re.fullmatch(r"/api/categories/[a-f0-9]{32}", path):
                result = library.category(data, identifier)
                if result:
                    return self._response(200, result)
        elif method == "DELETE":
            if path == "/api/sync/session":
                self.sync.clear_session()
                return self._response(200, {"deleted": True})
            if re.fullmatch(r"/api/reels/[a-f0-9]{32}", path) and library.delete(path.rsplit("/", 1)[-1]):
                return self._response(200, {"deleted": True})
        raise RequestError(404, "Cette ressource est introuvable.")

    def __call__(self, environ, start_response):
        try:
            status, headers, body = self._dispatch(environ)
        except RequestError as error:
            status, headers, body = self._response(error.status, {"error": error.message})
        except (ValidationError, SyncError) as error:
            status, headers, body = self._response(400, {"error": str(error)})
        except Exception:
            logging.exception("Erreur du serveur de bibliothèque")
            status, headers, body = self._response(500, {"error": "Une erreur interne est survenue. Consulte les journaux du serveur."})
        start_response(f"{status} {HTTPStatus(status).phrase}", headers)
        return [body]

    def close(self):
        self.sync.close()
