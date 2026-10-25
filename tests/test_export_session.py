import io
import logging
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.cookiejar import Cookie
from pathlib import Path
from unittest.mock import Mock, patch

from reels_library.export_session import CookieReadError, main, read_browser_cookies


def fake_cookie():
    return Cookie(0, "sessionid", "FAKE_COOKIE_FOR_EXPORT_TEST", None, False, ".instagram.com", True, True,
                  "/", True, True, 2147483647, False, None, None, {})


class ExportSessionTests(unittest.TestCase):
    def test_profile_and_instagram_domain_are_forwarded_without_reading_real_cookies(self):
        loader = Mock(return_value=[fake_cookie()])
        result = read_browser_cookies("chrome", "Profile 1", loader)
        loader.assert_called_once_with(("chrome", "Profile 1", None, None, ".instagram.com"))
        self.assertEqual(result[0].name, "sessionid")

    def test_decryption_failure_explains_chrome_limitation_without_exposing_logs(self):
        stream = io.StringIO()

        def blocked_loader(specification):
            logging.getLogger("cookies").warning("Failed to decrypt cookie (DPAPI): %s", "DO_NOT_PRINT_COOKIE_VALUE")
            raise AttributeError("DO_NOT_PRINT_EXCEPTION_VALUE")

        with patch("reels_library.export_session.sys.platform", "win32"), redirect_stderr(stream):
            with self.assertRaises(CookieReadError) as caught:
                read_browser_cookies("chrome", loader=blocked_loader)
        self.assertIn("COOKIES_DECRYPTION_FAILED", str(caught.exception))
        self.assertIn("App-Bound Encryption", str(caught.exception))
        self.assertNotIn("DO_NOT_PRINT", str(caught.exception) + stream.getvalue())

    def test_locked_and_missing_profile_have_different_safe_diagnostics(self):
        for exception, code in [(PermissionError("PRIVATE_PATH"), "COOKIES_LOCKED"),
                                (sqlite3.OperationalError("database is locked PRIVATE_DATA"), "COOKIES_LOCKED"),
                                (FileNotFoundError("PRIVATE_PATH"), "COOKIES_PROFILE_NOT_FOUND")]:
            with self.subTest(code=code), self.assertRaises(CookieReadError) as caught:
                read_browser_cookies("chrome", loader=Mock(side_effect=exception))
            self.assertIn(code, str(caught.exception))
            self.assertNotIn("PRIVATE", str(caught.exception))

    def test_unexpected_error_details_are_not_printed(self):
        with self.assertRaises(CookieReadError) as caught:
            read_browser_cookies("chrome", loader=Mock(side_effect=RuntimeError("SESSION_SECRET")))
        self.assertIn("COOKIES_READ_FAILED", str(caught.exception))
        self.assertNotIn("SESSION_SECRET", str(caught.exception))

    def test_empty_profile_distinguishes_missing_login_from_decryption(self):
        with self.assertRaisesRegex(CookieReadError, "INSTAGRAM_SESSION_MISSING"):
            read_browser_cookies("firefox", loader=Mock(return_value=[]))

    def test_failed_decryption_warning_also_handles_skipped_cookies(self):
        def empty_loader(specification):
            logging.getLogger("cookies").warning("Unable to decrypt cookies: PRIVATE_KEY")
            return []

        with self.assertRaisesRegex(CookieReadError, "COOKIES_DECRYPTION_FAILED"):
            read_browser_cookies("chrome", loader=empty_loader)

    def test_existing_logging_configuration_is_restored_and_private_messages_are_intercepted(self):
        logger = logging.getLogger("cookies")
        previous = (logger.handlers[:], logger.level, logger.propagate, logger.disabled)
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        try:
            logger.handlers = [handler]
            logger.setLevel(logging.ERROR)
            logger.propagate = True
            logger.disabled = False

            def loader(specification):
                logger.warning("PRIVATE_COOKIE_METADATA")
                return [fake_cookie()]

            read_browser_cookies("firefox", loader=loader)
            self.assertEqual(stream.getvalue(), "")
            self.assertEqual(logger.handlers, [handler])
            self.assertEqual(logger.level, logging.ERROR)
            self.assertTrue(logger.propagate)
        finally:
            logger.handlers, level, logger.propagate, logger.disabled = previous
            logger.setLevel(level)
            handler.close()

    def test_cli_exports_mocked_session_with_profile_and_without_printing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "session.cookies"
            stream = io.StringIO()
            with patch("sys.argv", ["export_session", "--browser", "chrome", "--profile", "Default", "--output", str(output)]), patch("reels_library.export_session.read_browser_cookies", return_value=[fake_cookie()]) as reader, redirect_stdout(stream):
                main()
            reader.assert_called_once_with("chrome", "Default")
            self.assertTrue(output.is_file())
            self.assertIn("FAKE_COOKIE_FOR_EXPORT_TEST", output.read_text(encoding="utf-8"))
            self.assertNotIn("FAKE_COOKIE_FOR_EXPORT_TEST", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
