import os
import tempfile
import unittest
from pathlib import Path

from reels_library.access_key import configured_key, ensure_key
from reels_library.domain import ValidationError


class AccessKeyTests(unittest.TestCase):
    def test_new_install_creates_a_persistent_private_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config" / "app_token"
            environment = {"REELS_ACCESS_TOKEN_FILE": str(path), "REELS_CREATE_ACCESS_TOKEN": "true"}
            first = configured_key(environment)
            self.assertGreaterEqual(len(first), 32)
            self.assertEqual(configured_key(environment), first)
            self.assertEqual(path.read_text().strip(), first)
            if os.name != "nt":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_two_installations_have_different_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertNotEqual(ensure_key(root / "one" / "key"), ensure_key(root / "two" / "key"))

    def test_invalid_existing_key_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_text("invalid", encoding="ascii")
            with self.assertRaises(ValidationError):
                ensure_key(path)
            self.assertEqual(path.read_text(), "invalid")

    def test_creation_is_explicit_and_requires_a_file(self):
        self.assertIsNone(configured_key({}))
        self.assertEqual(configured_key({"REELS_ACCESS_TOKEN": "x" * 32}), "x" * 32)
        with self.assertRaises(ValidationError):
            configured_key({"REELS_CREATE_ACCESS_TOKEN": "true"})
        with self.assertRaises(ValidationError):
            configured_key({"REELS_CREATE_ACCESS_TOKEN": "typo"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            with self.assertRaises(FileNotFoundError):
                configured_key({"REELS_ACCESS_TOKEN_FILE": str(path)})
            self.assertFalse(path.exists())

    def test_managed_file_has_precedence_over_environment_token(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_text("managed-" + "x" * 32, encoding="ascii")
            self.assertEqual(configured_key({"REELS_ACCESS_TOKEN_FILE": str(path), "REELS_ACCESS_TOKEN": "other-" + "y" * 32}), path.read_text())
