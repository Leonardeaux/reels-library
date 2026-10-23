import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from reels_library.database import Library
from reels_library.domain import ValidationError, normalize_url
from reels_library.importers import parse_import


class URLTests(unittest.TestCase):
    def test_normalization_strips_tracking_but_preserves_shortcode_case(self):
        url, identifier = normalize_url(" https://m.instagram.com/reels/Ab_C-12/?igsh=tracking#foo ")
        self.assertEqual(url, "https://www.instagram.com/reel/Ab_C-12/")
        self.assertEqual(identifier, "instagram:Ab_C-12")
        self.assertEqual(normalize_url("instagram.com/p/Ab_C-12/")[1], identifier)
        self.assertNotEqual(normalize_url("instagram.com/reel/ab_C-12/")[1], identifier)

    def test_rejects_foreign_hosts_credentials_shortlinks_and_non_publication_paths(self):
        for url in ["https://instagram.com.evil.test/reel/abc/", "https://evil.test/instagram.com/reel/abc/",
                    "https://user:password@instagram.com/reel/abc/", "file:///reel/abc/", "javascript:alert(1)",
                    "https://instagram.com:443/reel/abc/", "https://instagram.com/creator/", "https://instagram.com/share/reel/abc/",
                    "https://instagram.com/reel/abc/extra", "https://instagram.com/reel/a\nbc/", "http://[invalid"]:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                normalize_url(url)


class ImportParserTests(unittest.TestCase):
    def test_meta_map_and_list_formats_preserve_saved_dates_and_collections(self):
        entries = [{"title": "alice", "string_map_data": {"Saved on": {"href": "https://instagram.com/reel/ABC/", "timestamp": 1700000000}}, "collections": ["À cuisiner"]},
                   {"string_list_data": [{"href": "https://instagram.com/p/XYZ/", "timestamp": 1700000001}]}]
        for key in ("saved_saved_media", "saved_media", "saved_posts", "items"):
            result = parse_import(json.dumps({key: entries}), "saved.json")
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].collections, ["À cuisiner"])
            self.assertTrue(result[0].saved_at.startswith("2023-11-14"))
            self.assertEqual(result[1].source_id, "instagram:XYZ")

    def test_each_broken_entry_is_retained_in_accounting(self):
        result = parse_import(json.dumps([{}, 42, {"url": "https://example.com/a"}, {"url": "https://instagram.com/reel/ABC/", "saved_at": "invalid"}]))
        self.assertEqual(len(result), 4)
        self.assertTrue(all(candidate.problem for candidate in result))
        self.assertEqual(result[-1].problem_status, "error")

    def test_text_keeps_line_numbers_and_does_not_discard_duplicates(self):
        result = parse_import("# commentaire\n\nhttps://instagram.com/reel/ABC/\nhttps://instagram.com/reel/ABC/\ninvalide", "links.txt")
        self.assertEqual([candidate.position for candidate in result], [3, 4, 5])
        self.assertEqual(len(result), 3)
        self.assertTrue(result[-1].problem)

    def test_rejects_unknown_malformed_and_whole_account_exports(self):
        for content in ["{broken", '{"profile":{"href":"https://instagram.com/reel/ABC/"}}', '"text"']:
            with self.subTest(content=content), self.assertRaises(ValidationError):
                parse_import(content, "saved.json")
        with self.assertRaises(ValidationError):
            parse_import("<html>not supported</html>", "saved.html")


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "library.sqlite3"
        self.library = Library(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def add(self, code="ABC", **values):
        return self.library.create({"url": f"https://instagram.com/reel/{code}/", **values})["id"]

    def test_preview_is_read_only_and_duplicate_detection_uses_normalized_identity(self):
        content = "https://instagram.com/reels/ABC/?igsh=one\nhttps://www.instagram.com/p/ABC/\nhttps://instagram.com/reel/XYZ/\nnot-a-link"
        preview = self.library.import_content(content, "links.txt", preview=True)
        self.assertEqual((preview["imported"], preview["duplicate"], preview["ignored"]), (2, 1, 1))
        self.assertEqual(self.library.list()["stats"]["total"], 0)
        self.assertEqual(self.library.import_history(), [])
        actual = self.library.import_content(content, "links.txt")
        self.assertEqual(actual["total"], sum(actual[key] for key in ("imported", "duplicate", "ignored", "error")))
        self.assertEqual(self.library.list()["stats"]["total"], 2)
        self.assertEqual(len(self.library.import_history()), 1)

    def test_reimport_never_overwrites_corrections_or_duplicates_source_records(self):
        content = json.dumps({"saved_saved_media": [{"url": "https://instagram.com/reel/ABC/", "title": "Source title", "caption": "Original text"}]})
        self.library.import_content(content, "saved.json")
        identifier = self.library.list()["reels"][0]["id"]
        self.library.update(identifier, {"title": "Mon titre", "notes": "Une correction", "categories": ["Robotique", "Impression 3D"], "stage": "used", "summary": "Ma synthèse"})
        report = self.library.import_content(content, "saved.json")
        reel = self.library.get(identifier)
        self.assertEqual(report["duplicate"], 1)
        self.assertEqual(reel["title"], "Mon titre")
        self.assertEqual(reel["notes"], "Une correction")
        self.assertEqual(reel["summary"], "Ma synthèse")
        self.assertEqual(reel["stage"], "used")
        self.assertEqual(set(reel["categories"]), {"Robotique", "Impression 3D"})
        self.assertEqual(reel["sources"][0]["raw"]["title"], "Source title")
        self.assertEqual(len(reel["sources"]), 1)

    def test_manual_duplicate_keeps_existing_fiche(self):
        identifier = self.add(title="Keep me")
        duplicate = self.library.create({"url": "https://www.instagram.com/p/ABC/?igsh=foo", "title": "Overwrite"})
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["id"], identifier)
        self.assertEqual(self.library.get(identifier)["title"], "Keep me")

    def test_manual_source_revisions_can_be_reverted_or_cleared_without_losing_raw_sources(self):
        identifier = self.add(source_text="Version A")
        self.library.update(identifier, {"source_text": "Version B"})
        self.library.update(identifier, {"source_text": "Version A"})
        self.assertEqual(self.library.get(identifier)["source_text"], "Version A")
        self.library.update(identifier, {"source_text": ""})
        reel = self.library.get(identifier)
        self.assertEqual(reel["source_text"], "")
        self.assertEqual(reel["technical_status"], "reference_only")
        self.assertEqual([source["text"] for source in reel["sources"] if source["kind"] == "manual"], ["Version A", "Version B", "Version A", ""])

    def test_search_is_accent_insensitive_and_covers_notes_sources_categories_collections(self):
        identifier = self.add(title="Crème brûlée", source_text="Robotique", notes="Avec un chalumeau", categories=["Cuisine"], tags=["Rapide"], collections=["Été 2027"])
        for query in ("creme brulee", "CHALUMEAU", "robotique", "cuisine rapide", "ete 2027"):
            with self.subTest(query=query):
                self.assertEqual([item["id"] for item in self.library.list({"q": query})["reels"]], [identifier])
        self.assertEqual(self.library.list({"q": "other"})["reels"], [])

    def test_personal_status_is_independent_from_technical_coverage(self):
        first = self.add(stage="used", intention="cook", starred=True, categories=["Cuisine"])
        second = self.add("XYZ", stage="in_progress", source_text="Du texte")
        self.assertEqual(self.library.get(first)["technical_status"], "reference_only")
        self.assertEqual(self.library.get(second)["technical_status"], "text_available")
        self.assertEqual(len(self.library.list({"starred": "1", "stage": "used", "intention": "cook"})["reels"]), 1)
        self.assertEqual(len(self.library.list({"category": "__unclassified__"})["reels"]), 1)
        self.assertEqual(len(self.library.list({"technical_status": "text_available"})["reels"]), 1)

    def test_categories_can_be_renamed_and_archived_without_losing_associations(self):
        identifier = self.add(categories=["Robotique"])
        category = next(item for item in self.library.list()["categories"] if item["name"] == "Robotique")
        self.library.category({"name": "Robots", "archived": True}, category["id"])
        self.assertEqual(self.library.get(identifier)["categories"], ["Robots"])
        self.assertEqual(len(self.library.list({"category": "Robots"})["reels"]), 1)
        existing = next(item for item in self.library.list()["categories"] if item["id"] == category["id"])
        self.assertTrue(existing["archived"])

    def test_invalid_update_is_atomic(self):
        identifier = self.add(title="Original")
        for invalid in [{"title": "Modified", "stage": "invalid"}, {"starred": "false"}, {"tags": "not-a-list"}, {"notes": None}]:
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                self.library.update(identifier, invalid)
        self.assertEqual(self.library.get(identifier)["title"], "Original")

    def test_export_can_be_reimported_with_notes_classification_and_source_provenance(self):
        identifier = self.add(title="À garder", source_text="Original", notes="Mes notes", summary="Synthèse", categories=["IA", "DIY"], tags=["Essai"], collections=["Projets été"], stage="in_progress", starred=True)
        self.library.update(identifier, {"source_text": "Correction"})
        exported = self.library.export()
        other = Library(Path(self.temp.name) / "restored.sqlite3")
        report = other.import_content(json.dumps(exported), "reels-library.json")
        self.assertEqual(report["imported"], 1)
        restored = other.list()["reels"][0]
        original = self.library.get(identifier)
        for key in ("url", "title", "source_text", "notes", "summary", "categories", "tags", "collections", "stage", "starred", "imported_at", "updated_at"):
            self.assertEqual(restored[key], original[key], key)
        self.assertEqual(len(other.get(restored["id"])["sources"]), len(original["sources"]))
        self.assertEqual(other.import_content(json.dumps(exported), "reels-library.json")["duplicate"], 1)

    def test_later_import_can_add_source_text_without_overwriting_manual_corrections(self):
        identifier = self.add(title="Mon titre", notes="Mes notes")
        report = self.library.import_content(json.dumps([{"url": "https://instagram.com/reel/ABC/", "caption": "Nouvelle légende"}]), "saved.json")
        self.assertEqual(report["duplicate"], 1)
        reel = self.library.get(identifier)
        self.assertEqual(reel["source_text"], "Nouvelle légende")
        self.assertEqual(reel["title"], "Mon titre")
        self.library.update(identifier, {"source_text": "Ma correction"})
        self.library.import_content(json.dumps([{"url": "https://instagram.com/reel/ABC/", "caption": "Autre légende"}]), "saved.json")
        self.assertEqual(self.library.get(identifier)["source_text"], "Ma correction")

    def test_simultaneous_imports_are_serialized_before_duplicate_detection(self):
        content = "https://instagram.com/reel/CONCURRENT/"
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.library.import_content(content, "links.txt"), range(2)))
        self.assertEqual(sum(result["imported"] for result in results), 1)
        self.assertEqual(sum(result["duplicate"] for result in results), 1)
        self.assertEqual(self.library.list()["stats"]["total"], 1)

    def test_deletion_removes_sources_and_references_but_keeps_import_accounting(self):
        self.library.import_content("https://instagram.com/reel/ABC/", "links.txt")
        identifier = self.library.list()["reels"][0]["id"]
        self.assertTrue(self.library.delete(identifier))
        self.assertIsNone(self.library.get(identifier))
        with self.library.connection() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM sources").fetchone()[0], 0)
            entry = connection.execute("SELECT * FROM import_entries").fetchone()
            self.assertIsNone(entry["reel_id"])
        self.assertEqual(self.library.import_history()[0]["imported"], 1)

    def test_data_persists_after_reopening(self):
        identifier = self.add(title="Persistant")
        reopened = Library(self.path)
        self.assertEqual(reopened.get(identifier)["title"], "Persistant")


if __name__ == "__main__":
    unittest.main()
