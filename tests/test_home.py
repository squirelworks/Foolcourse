"""The portable app opens the courses folder you filled, and does not ask."""

import os
import tempfile
import unittest
from pathlib import Path

from foolcourse.home import (
    fit_geometry,
    holds_books,
    load_window,
    remember_window,
    resolve_courses,
    screen_geometry,
)


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


class WindowTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("FOOLCOURSE_HOME", None)

    def test_first_window_tracks_the_screen(self):
        wide = screen_geometry(1920, 1080)
        self.assertTrue(wide.startswith("1689x907+"))
        small = screen_geometry(1280, 800)
        self.assertLess(int(small.split("x")[0]), 1280)
        self.assertGreater(int(small.split("x")[1].split("+")[0]), 640)

    def test_a_saved_window_comes_back(self):
        self.assertEqual(fit_geometry("1600x900+40+30", 0, 0, 1920, 1080), "1600x900+40+30")
        self.assertIsNone(fit_geometry("1600x900+4000+30", 0, 0, 1920, 1080))
        shrunk = fit_geometry("3000x2000+10+10", 0, 0, 1920, 1080)
        self.assertEqual(shrunk, "1920x1080+10+10")

    def test_window_layout_is_remembered(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["FOOLCOURSE_HOME"] = tmp
            remember_window("1600x900+20+20", True, {"3": [400, 900]})
            saved = load_window()
            self.assertEqual(saved["geometry"], "1600x900+20+20")
            self.assertTrue(saved["zoomed"])
            self.assertEqual(saved["sashes"]["3"], [400, 900])


if __name__ == "__main__":
    unittest.main()
