import http.client
import base64
import json
import tempfile
import threading
import unittest
from pathlib import Path

from reels_library.server import make_server
from reels_library.web import Application, validate_public_url
from reels_library.domain import ValidationError
from tests.test_sync import session_fixture


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = make_server(Path(cls.temp.name) / "library.sqlite3", port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, data=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        request_headers = {"Content-Type": "application/json"} if data is not None else {}
        request_headers.update(headers or {})
        body = json.dumps(data) if data is not None else None
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        result = (response.status, dict(response.getheaders()), response.read())
        connection.close()
        return result

    def test_full_add_edit_search_export_delete_flow(self):
        status, _, body = self.request("POST", "/api/reels", {"url": "https://instagram.com/reel/APItest/", "title": "Test API"})
        self.assertEqual(status, 201)
        identifier = json.loads(body)["id"]
        status, _, _ = self.request("PATCH", f"/api/reels/{identifier}", {"notes": "retrouvable", "categories": ["Test API"], "stage": "used"})
        self.assertEqual(status, 200)
        status, _, body = self.request("GET", "/api/library?q=retrouvable")
        self.assertEqual(len(json.loads(body)["reels"]), 1)
        status, headers, body = self.request("GET", "/api/export")
        self.assertEqual(status, 200)
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertEqual(json.loads(body)["format"], "reels-library")
        self.assertEqual(self.request("DELETE", f"/api/reels/{identifier}")[0], 200)
        self.assertEqual(self.request("GET", f"/api/reels/{identifier}")[0], 404)

    def test_import_preview_and_commit(self):
        payload = {"content": "https://instagram.com/reel/APIimport/\ninvalid", "filename": "links.txt"}
        status, _, body = self.request("POST", "/api/import/preview", payload)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["ignored"], 1)
        status, _, body = self.request("POST", "/api/import", payload)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["imported"], 1)

    def test_rejects_cross_origin_and_dns_rebinding(self):
        self.assertEqual(self.request("GET", "/api/library", headers={"Host": "evil.test"})[0], 403)
        self.assertEqual(self.request("GET", "/api/export", headers={"Origin": "https://evil.test"})[0], 403)
        self.assertEqual(self.request("POST", "/api/reels", {"url": "https://instagram.com/reel/UNSAFE/"}, {"Sec-Fetch-Site": "cross-site"})[0], 403)

    def test_validation_errors_are_json_and_do_not_mutate(self):
        status, _, body = self.request("POST", "/api/reels", {"url": "https://example.com/"})
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(body))
        self.assertEqual(self.request("POST", "/api/reels", {}, {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/reels", ["invalid"])[0], 400)

    def test_only_explicit_static_assets_are_served_and_csp_is_present(self):
        for path in ("/", "/app.js", "/styles.css", "/favicon.svg"):
            status, headers, body = self.request("GET", path)
            self.assertEqual(status, 200, path)
            self.assertTrue(body)
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for path in ("/data/library.sqlite3", "/.git/config", "/../README.md", "/static/../../README.md"):
            self.assertEqual(self.request("GET", path)[0], 404, path)

    def test_xss_payload_is_returned_as_data(self):
        payload = '<img src=x onerror="alert(1)">'
        status, _, body = self.request("POST", "/api/reels", {"url": "https://instagram.com/reel/APIscript/", "title": payload})
        identifier = json.loads(body)["id"]
        status, headers, body = self.request("GET", f"/api/reels/{identifier}")
        self.assertTrue(headers["Content-Type"].startswith("application/json"))
        self.assertEqual(json.loads(body)["title"], payload)
        self.request("DELETE", f"/api/reels/{identifier}")

    def test_session_upload_status_and_removal_never_return_session_values(self):
        status, _, body = self.request("POST", "/api/sync/session", {"content": session_fixture()})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["configured"])
        status, _, body = self.request("GET", "/api/sync")
        self.assertNotIn(b"FAKE_SESSION_FOR_TESTS", body)
        self.assertTrue(json.loads(body)["session"]["configured"])
        self.assertEqual(self.request("DELETE", "/api/sync/session")[0], 200)
        self.assertFalse(self.server.sync.settings()["enabled"])


class RemoteAuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.token = "test-access-key-" + "x" * 32
        cls.server = make_server(Path(cls.temp.name) / "library.sqlite3", port=0, access_token=cls.token)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path, authorization=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request("GET", path, headers={"Authorization": authorization} if authorization else {})
        response = connection.getresponse()
        result = (response.status, dict(response.getheaders()), response.read())
        connection.close()
        return result

    def test_library_export_session_status_and_static_page_require_authentication(self):
        for path in ("/", "/api/library", "/api/export", "/api/sync"):
            status, headers, _ = self.request(path)
            self.assertEqual(status, 401, path)
            self.assertIn("Basic", headers["WWW-Authenticate"])
        self.assertEqual(self.request("/api/health")[0], 200)

    def test_basic_and_bearer_authentication_work_and_malformed_credentials_fail_closed(self):
        basic = "Basic " + base64.b64encode(("admin:" + self.token).encode()).decode()
        self.assertEqual(self.request("/api/library", basic)[0], 200)
        self.assertEqual(self.request("/api/library", "Bearer " + self.token)[0], 200)
        for authorization in ("Basic malformed@@", "Bearer wrong", "Basic " + base64.b64encode(b"wrong:password").decode()):
            self.assertEqual(self.request("/api/library", authorization)[0], 401)

    def test_public_configuration_requires_https_and_an_access_key(self):
        with self.assertRaises(ValidationError):
            validate_public_url("http://reels.example.test")
        with self.assertRaises(ValidationError):
            Application(Path(self.temp.name) / "remote.sqlite3", public_url="https://reels.example.test")
        with self.assertRaises(ValidationError):
            Application(Path(self.temp.name) / "remote.sqlite3", access_token="weak")


if __name__ == "__main__":
    unittest.main()
