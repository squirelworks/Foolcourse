"""The portable app opens the courses folder you filled, and does not ask."""

import os
import tempfile
import unittest
from pathlib import Path

from foolcourse.home import holds_books, resolve_courses


class HomeTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("FOOLCOURSE_HOME", None)

    def test_books_dropped_in_courses_are_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            courses = root / "courses" / "DC Circuits"
            courses.mkdir(parents=True)
            (courses / "lesson.tbk").write_bytes(b"x")
            os.environ["FOOLCOURSE_HOME"] = str(root)
            found = resolve_courses(None, ask=True)
            self.assertTrue(holds_books(root / "courses"))
            self.assertEqual(found, (root / "courses").resolve())

    def test_a_remembered_folder_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            courses = root / "courses"
            courses.mkdir()
            (courses / "lesson.tbk").write_bytes(b"x")
            other = root / "other"
            other.mkdir()
            os.environ["FOOLCOURSE_HOME"] = str(root)
            from foolcourse.home import remember_courses
            remember_courses(other)
            self.assertEqual(resolve_courses(None, ask=False), other.resolve())


if __name__ == "__main__":
    unittest.main()
