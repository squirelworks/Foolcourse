"""A published folder's books.json gives the course list its titles and page counts."""

import json
import tempfile
import unittest
from pathlib import Path

from foolcourse.catalog import scan


def _courses(catalog):
    return {c["id"]: c for s in catalog["subjects"] for m in s["modules"] for c in m["courses"]}


class BooksJson(unittest.TestCase):
    def test_titles_and_page_counts_come_from_books_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "Maths"
            folder.mkdir()
            (folder / "fractions.fbk").write_bytes(b"not read")
            (folder / "decimals.fbk").write_bytes(b"not read")
            (folder / "books.json").write_text(json.dumps({"books": [
                {"title": "Fractions", "file": "fractions.fbk", "pages": 3}]}))
            courses = _courses(scan(Path(tmp)))
            self.assertEqual((courses["fractions"]["title"], courses["fractions"]["pages"]), ("Fractions", 3))
            self.assertEqual(courses["decimals"]["title"], "decimals")
            self.assertNotIn("pages", courses["decimals"])

    def test_a_bad_books_json_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "one.fbk").write_bytes(b"x")
            (Path(tmp) / "books.json").write_text("not json")
            self.assertEqual(_courses(scan(Path(tmp)))["one"]["title"], "one")


if __name__ == "__main__":
    unittest.main()
