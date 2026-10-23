import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from reels_library.database import Library
from reels_library.domain import ValidationError
from reels_library.session import SessionStore, clean_cookies
from reels_library.sync import SyncError, SyncManager, connector_command, parse_connector_output, validate_settings


def session_fixture(value="FAKE_SESSION_FOR_TESTS"):
    return "# Netscape HTTP Cookie File\n.instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\t" + value + "\n"


class SessionTests(unittest.TestCase):
    def test_only_instagram_cookies_are_kept(self):
        content = session_fixture() + ".unrelated.test\tTRUE\t/\tTRUE\t2147483647\tprivate\tUNRELATED_SECRET\n"
        cleaned = clean_cookies(content)
        self.assertIn("FAKE_SESSION_FOR_TESTS", cleaned)
        self.assertNotIn("UNRELATED_SECRET", cleaned)
        self.assertNotIn("unrelated.test", cleaned)

    def test_missing_expired_malformed_and_oversized_sessions_are_rejected(self):
        for content in ["", "not cookies", session_fixture().replace("2147483647", "1"),
                        session_fixture().replace("sessionid", "csrftoken"), "a" * (128 * 1024 + 1)]:
            with self.subTest(length=len(content)), self.assertRaises(ValidationError):
                clean_cookies(content)

    def test_http_only_prefix_and_session_cookies_are_accepted(self):
        content = session_fixture().replace(".instagram.com", "#HttpOnly_.instagram.com").replace("2147483647", "0")
        self.assertIn("#HttpOnly_.instagram.com", clean_cookies(content))

    def test_store_preserves_valid_session_on_invalid_replacement_and_never_returns_secrets(self):
        with tempfile.TemporaryDirectory() as root:
            store = SessionStore(Path(root) / "sessions" / "instagram.cookies")
            self.assertFalse(store.status()["configured"])
            result = store.install(session_fixture())
            self.assertTrue(result["configured"])
            self.assertNotIn("FAKE_SESSION_FOR_TESTS", json.dumps(result))
            with self.assertRaises(ValidationError):
                store.install("invalid")
            self.assertTrue(store.status()["configured"])
            if os.name != "nt":
                self.assertEqual(store.path.stat().st_mode & 0o777, 0o600)
            store.clear()
            self.assertFalse(store.status()["configured"])


class ConnectorTests(unittest.TestCase):
    def test_parsing_is_per_publication_and_stores_only_explicit_metadata(self):
        meta = {"post_url": "https://instagram.com/reel/ABC/", "description": "Une légende\nTexte complet", "username": "alice", "post_date": "2026-01-01T12:00:00", "sessionid": "DO_NOT_KEEP", "video_url": "https://cdn.example.test/private"}
        result = parse_connector_output(json.dumps([[2, meta], [3, "https://cdn.example.test/private", meta], [2, meta]]))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Une légende")
        self.assertEqual(result[0]["caption"], meta["description"])
        self.assertNotIn("saved_at", result[0])
        self.assertNotIn("DO_NOT_KEEP", json.dumps(result))
        self.assertNotIn("cdn.example", json.dumps(result))

    def test_embedded_error_is_a_failure_even_after_successful_records(self):
        messages = [[2, {"post_url": "https://instagram.com/reel/ABC/"}], [-1, {"error": "AuthError", "message": "SECRET_DETAILS"}]]
        with self.assertRaises(SyncError) as caught:
            parse_connector_output(json.dumps(messages))
        self.assertNotIn("SECRET_DETAILS", str(caught.exception))

    def test_rate_limit_is_reported_and_malformed_output_is_rejected(self):
        with self.assertRaisesRegex(SyncError, "limite les requêtes"):
            parse_connector_output(json.dumps([[-1, {"message": "HTTP 429"}]]))
        for output in ("not-json", "{}", '[null]', '[[2,{}]]'):
            with self.subTest(output=output), self.assertRaises(SyncError):
                parse_connector_output(output)

    def test_container_command_uses_a_session_file_without_a_browser_or_downloads(self):
        with patch("reels_library.sync.connector_python", return_value="python"):
            command = connector_command({"limit": 50}, Path("/sessions/instagram.cookies"))
        self.assertIn("--cookies", command)
        self.assertIn("--no-download", command)
        self.assertIn("--config-ignore", command)
        self.assertNotIn("--cookies-from-browser", command)
        self.assertNotIn("FAKE_SESSION_FOR_TESTS", " ".join(command))


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.library = Library(Path(self.temp.name) / "library.sqlite3")
        self.manager = SyncManager(self.library, Path(self.temp.name) / "private" / "instagram.cookies")

    def tearDown(self):
        self.manager.close()
        self.temp.cleanup()

    def run_mocked(self, messages, returncode=0):
        process = MagicMock()
        process.returncode = returncode
        process.communicate.return_value = (json.dumps(messages).encode(), b"NEVER_LOG_THIS")
        process.poll.return_value = returncode
        with patch("reels_library.sync.connector_python", return_value="python"), patch("reels_library.sync.subprocess.Popen", return_value=process):
            self.manager.start()
            self.manager.thread.join(timeout=5)
            self.assertFalse(self.manager.running)
        return self.manager.status()["runs"][0]

    def test_missing_session_prevents_automatic_sync_and_manual_start(self):
        with self.assertRaises(ValidationError):
            self.manager.configure({"enabled": True})
        with self.assertRaises(SyncError):
            self.manager.start()

    def test_successful_runs_import_and_reimport_without_overwriting_personal_notes(self):
        self.manager.install_session(session_fixture())
        messages = [[2, {"post_url": "https://instagram.com/reel/ABC/", "description": "Légende source", "username": "alice"}]]
        first = self.run_mocked(messages)
        self.assertEqual(first["status"], "success")
        self.assertEqual(first["imported"], 1)
        identifier = self.library.list()["reels"][0]["id"]
        self.library.update(identifier, {"title": "Ma correction", "notes": "À conserver"})
        second = self.run_mocked(messages)
        self.assertEqual(second["duplicate"], 1)
        self.assertEqual(self.library.get(identifier)["title"], "Ma correction")
        self.assertEqual(self.library.get(identifier)["notes"], "À conserver")
        self.assertNotIn("FAKE_SESSION_FOR_TESTS", json.dumps(self.library.export()))

    def test_failed_partial_response_is_not_imported_and_error_details_are_redacted(self):
        self.manager.install_session(session_fixture())
        run = self.run_mocked([[2, {"post_url": "https://instagram.com/reel/ABC/"}], [-1, {"message": "PRIVATE_ERROR_DETAILS"}]])
        self.assertEqual(run["status"], "error")
        self.assertEqual(self.library.list()["stats"]["total"], 0)
        self.assertNotIn("PRIVATE_ERROR_DETAILS", run["message"])
        self.assertNotIn("NEVER_LOG_THIS", run["message"])

    def test_scheduled_settings_survive_restart_and_clearing_session_disables_them(self):
        self.manager.install_session(session_fixture())
        self.manager.configure({"enabled": True, "interval_minutes": 360, "limit": 200})
        self.assertIsNotNone(self.manager.next_run)
        reopened = SyncManager(self.library, self.manager.session.path)
        try:
            self.assertTrue(reopened.settings()["enabled"])
            self.assertEqual(reopened.settings()["limit"], 200)
            reopened.clear_session()
            self.assertFalse(reopened.settings()["enabled"])
            self.assertIsNone(reopened.next_run)
        finally:
            reopened.close()

    def test_previous_running_job_is_marked_interrupted(self):
        with self.library.connection() as connection:
            connection.execute("INSERT INTO sync_runs(id,started_at,status) VALUES('old','2026-10-23T12:00:00+00:00','running')")
        reopened = SyncManager(self.library, self.manager.session.path)
        try:
            self.assertEqual(reopened.status()["runs"][0]["status"], "interrupted")
        finally:
            reopened.close()

    def test_scheduler_resumes_persisted_enabled_settings_without_a_browser(self):
        self.manager.install_session(session_fixture())
        self.manager.configure({"enabled": True, "interval_minutes": 60, "limit": 50})
        called = threading.Event()

        def scheduled_start():
            self.manager.next_run = datetime.now(timezone.utc) + timedelta(hours=1)
            called.set()

        with patch.object(self.manager, "start", side_effect=scheduled_start):
            self.manager.start_scheduler()
            self.assertTrue(called.wait(timeout=4))

    def test_expired_session_failure_is_visible_in_scheduled_history(self):
        self.library.set_setting("sync", {"enabled": True, "interval_minutes": 60, "limit": 50})
        self.manager.start_scheduler()
        deadline = time.monotonic() + 4
        runs = []
        while time.monotonic() < deadline:
            runs = self.manager.status()["runs"]
            if runs:
                break
            self.manager.stop_event.wait(0.05)
        self.assertTrue(runs)
        self.assertEqual(runs[0]["status"], "error")
        self.assertIn("session Instagram", runs[0]["message"])

    def test_unsafe_settings_and_simultaneous_runs_are_rejected(self):
        for data in ({"interval_minutes": 1}, {"limit": 999999}, {"enabled": "yes"}, {"limit": True}):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate_settings(data)
        self.manager.running = True
        try:
            with self.assertRaises(ValidationError):
                self.manager.start()
            with self.assertRaises(ValidationError):
                self.manager.install_session(session_fixture())
        finally:
            self.manager.running = False
