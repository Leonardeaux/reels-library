"""Vérifier l'image Docker avec des données fictives et des volumes éphémères.

Aucune requête Instagram n'est envoyée. Seuls les objets Docker créés par ce
script, identifiés par un nom aléatoire, sont supprimés à la fin.
"""

import argparse
import http.client
import json
import secrets
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


def docker(*arguments, check=True):
    result = subprocess.run(["docker", *arguments], capture_output=True, text=True, check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "La commande Docker a échoué.")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="reels-library:dev")
    args = parser.parse_args()
    prefix = "reels-library-qa-" + uuid.uuid4().hex[:10]
    container, data_volume, session_volume = prefix, prefix + "-data", prefix + "-session"
    root = Path(__file__).resolve().parent.parent
    work = root / "work"
    work.mkdir(exist_ok=True)
    token = secrets.token_urlsafe(32)
    host = "reels.example.test"

    with tempfile.TemporaryDirectory(prefix="container-", dir=work) as directory:
        temporary = Path(directory).resolve()
        assert temporary.is_relative_to(work.resolve())
        token_file = temporary / "app_token"
        token_file.write_text(token, encoding="ascii")
        token_file.chmod(0o644)

        def start():
            docker("run", "-d", "--name", container, "--read-only", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:size=64m,mode=1777",
                   "--mount", f"type=bind,source={token_file},target=/run/secrets/app_token,readonly",
                   "--mount", f"type=volume,source={data_volume},target=/app/data",
                   "--mount", f"type=volume,source={session_volume},target=/app/sessions",
                   "-p", "127.0.0.1::8080", "-e", "REELS_PUBLIC_URL=https://" + host,
                   "-e", "REELS_ACCESS_TOKEN_FILE=/run/secrets/app_token", args.image)
            address = docker("port", container, "8080/tcp").stdout.strip()
            port = int(address.rsplit(":", 1)[1])
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                try:
                    status, body = request(port, "GET", "/api/health", authenticated=False)
                    if status == 200:
                        return port
                except (OSError, http.client.HTTPException):
                    pass
                time.sleep(0.2)
            raise RuntimeError("Le conteneur n'est pas devenu disponible.")

        def request(port, method, path, data=None, authenticated=True):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            headers = {"Host": host}
            if authenticated:
                headers["Authorization"] = "Bearer " + token
            if data is not None:
                headers["Content-Type"] = "application/json"
            connection.request(method, path, body=json.dumps(data) if data is not None else None, headers=headers)
            response = connection.getresponse()
            body = response.read()
            status = response.status
            connection.close()
            return status, json.loads(body)

        try:
            docker("volume", "create", data_volume)
            docker("volume", "create", session_volume)
            port = start()
            assert request(port, "GET", "/api/library", authenticated=False)[0] == 401
            assert request(port, "GET", "/api/library")[0] == 200
            assert docker("exec", container, "id", "-u").stdout.strip() == "10001"
            print("OK : serveur conteneurisé, accès privé et exécution sans root.")

            status, result = request(port, "POST", "/api/reels", {"url": "https://instagram.com/reel/CONTAINER_DEMO/", "title": "Donnée fictive persistante", "notes": "Conservée après recréation"})
            assert status == 201
            identifier = result["id"]
            fake_session = "# Netscape HTTP Cookie File\n.instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tFAKE_OFFLINE_TEST_SESSION\n"
            assert request(port, "POST", "/api/sync/session", {"content": fake_session})[0] == 200
            assert docker("exec", container, "stat", "-c", "%a", "/app/sessions/instagram.cookies").stdout.strip() == "600"
            assert request(port, "POST", "/api/sync/settings", {"enabled": False, "limit": 200, "interval_minutes": 360})[0] == 200
            status, exported = request(port, "GET", "/api/export")
            assert status == 200 and "FAKE_OFFLINE_TEST_SESSION" not in json.dumps(exported)
            print("OK : session séparée en mode 0600, absente de l'export de bibliothèque.")

            docker("stop", "--time", "10", container)
            docker("rm", container)
            port = start()
            status, reel = request(port, "GET", "/api/reels/" + identifier)
            assert status == 200 and reel["notes"] == "Conservée après recréation"
            status, sync = request(port, "GET", "/api/sync")
            assert status == 200 and sync["session"]["configured"] and sync["settings"]["limit"] == 200
            assert not sync["settings"]["enabled"]
            print("OK : bibliothèque, réglages et session conservés après recréation du conteneur.")

            result = docker("run", "--rm", "-e", "REELS_PUBLIC_URL=https://" + host, args.image, check=False)
            assert result.returncode != 0 and "clé d'accès" in result.stderr
            print("OK : démarrage distant refusé sans clé d'accès.")
            print("Aucune connexion Instagram effectuée.")
        finally:
            docker("stop", "--time", "10", container, check=False)
            docker("rm", "--force", container, check=False)
            docker("volume", "rm", data_volume, session_volume, check=False)


if __name__ == "__main__":
    main()
