"""Where a Foolcourse install keeps its own files.

The curriculum ships with the program. On Windows the books go in
``courses`` next to it. If that folder already has books, it is used.
"""

from __future__ import annotations

import os
import json
import re
import sys
from pathlib import Path


def portable() -> bool:
    """True when this run is the unzipped program, not a source checkout."""
    return bool(getattr(sys, "frozen", False) or os.environ.get("FOOLCOURSE_HOME"))


def app_dir() -> Path:
    """Folder the program was unpacked into.

    The curriculum and the student file live here, next to the launcher.
    """
    env = os.environ.get("FOOLCOURSE_HOME")
    if env:
        return Path(env).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def curriculum_dir() -> Path:
    return app_dir() / "_curriculum"


def student_dir() -> Path:
    dest = app_dir() / "_student"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _courses_file() -> Path:
    return student_dir() / "courses.path"


def remembered_courses() -> Path | None:
    """The courses folder chosen last time, if it is still there."""
    path = _courses_file()
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip().strip('"')
    if not text:
        return None
    folder = Path(text)
    return folder if folder.is_dir() else None


def remember_courses(folder: Path) -> None:
    _courses_file().write_text(str(Path(folder).resolve()) + "\n", encoding="utf-8")


_GEOM = re.compile(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$")


def screen_geometry(sw: int, sh: int) -> str:
    """First run: most of the screen, not a fixed 1280x640."""
    sw = max(int(sw), 1)
    sh = max(int(sh), 1)
    w = min(sw, max(900, int(sw * 0.88)))
    h = min(sh, max(420, int(sh * 0.84)))
    if sw > 960:
        w = min(w, sw - 48)
    if sh > 520:
        h = min(h, sh - 72)
    w = max(640, min(w, sw))
    h = max(400, min(h, sh))
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 8)
    return f"{w}x{h}+{x}+{y}"


def fit_geometry(geometry: str, vx: int, vy: int, vw: int, vh: int) -> str | None:
    """Put a saved window back, shrunk to the desktop. None if it would be off screen."""
    match = _GEOM.match((geometry or "").strip())
    if not match or vw < 200 or vh < 200:
        return None
    w, h = int(match.group(1)), int(match.group(2))
    x, y = int(match.group(3)), int(match.group(4))
    w = max(640, min(w, vw))
    h = max(400, min(h, vh))
    if x > vx + vw - 80 or y > vy + vh - 60:
        return None
    if x + min(w, 200) < vx or y + min(h, 80) < vy:
        return None
    return f"{w}x{h}{x:+d}{y:+d}"


def _sashes(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, value in raw.items():
        if not isinstance(value, list) or not value:
            continue
        positions = []
        for item in value:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                positions = []
                break
            positions.append(int(item))
        if positions:
            out[str(key)] = positions
    return out


def _window_file() -> Path:
    return student_dir() / "window.json"


def load_window() -> dict:
    """The last catalog window: size, whether it was maximized, column dividers."""
    path = _window_file()
    data = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded = {}
        if isinstance(loaded, dict):
            data = loaded
    geometry = data.get("geometry")
    return {
        "geometry": geometry if isinstance(geometry, str) else "",
        "zoomed": bool(data.get("zoomed")),
        "sashes": _sashes(data.get("sashes")),
    }


def remember_window(geometry: str | None, zoomed: bool, sashes: dict) -> None:
    body = {
        "geometry": geometry or "",
        "zoomed": bool(zoomed),
        "sashes": _sashes(sashes),
    }
    _window_file().write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def bundled_courses() -> Path:
    """The folder you drop books into, next to the program."""
    return app_dir() / "courses"


def holds_books(folder: Path) -> bool:
    """True when a folder, or a folder inside it, has a book."""
    if not folder.is_dir():
        return False
    suffixes = {".tbk", ".sbk", ".fbk", ".fsk", ".json"}
    try:
        children = list(folder.iterdir())
    except OSError:
        return False
    for child in children:
        if child.is_file() and child.suffix.lower() in suffixes:
            return True
        if not child.is_dir() or child.name.startswith("."):
            continue
        try:
            nested = child.rglob("*")
        except OSError:
            continue
        for item in nested:
            if item.is_file() and item.suffix.lower() in suffixes:
                return True
    return False


def dev_courses_root() -> Path:
    """Courses bundled with a source checkout. Not used by the portable app."""
    here = app_dir()
    pkg = Path(__file__).resolve().parent / "_courses"
    if pkg.exists():
        return pkg
    for name in ("_courses", "courses"):
        found = here / name
        if found.exists():
            return found
    return here / "_courses"


def ask_courses(locale: str = "en") -> Path | None:
    """Ask which folder holds the courses. None if the user cancels."""
    from foolcourse.locale import t
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except Exception:
        return None
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    messagebox.showinfo(t(locale, "app"), t(locale, "ask_courses"), parent=root)
    chosen = filedialog.askdirectory(title=t(locale, "ask_courses_title"), parent=root)
    root.destroy()
    if not chosen:
        return None
    folder = Path(chosen)
    return folder if folder.is_dir() else None


def resolve_courses(given: Path | None, *, ask: bool) -> Path:
    """A path on the command line wins. Otherwise use the remembered folder.

    A portable copy uses ``courses`` beside the program when that folder
    already has books, and does not ask. An empty one asks once. A source
    checkout uses its own ``_courses`` folder and does not ask.
    """
    if given is not None:
        folder = given.expanduser()
        if folder.is_dir():
            remember_courses(folder)
        return folder
    saved = remembered_courses()
    if saved is not None:
        return saved
    dropped = bundled_courses()
    if holds_books(dropped):
        remember_courses(dropped)
        return dropped
    if portable() and ask:
        chosen = ask_courses()
        if chosen is not None:
            remember_courses(chosen)
            return chosen
    if portable():
        dropped.mkdir(parents=True, exist_ok=True)
        return dropped
    return dev_courses_root()


def default_curriculum() -> Path | None:
    """The curriculum that belongs to this copy of the program.

    The example is preferred. Otherwise the first curriculum file in the folder.
    """
    folder = curriculum_dir()
    if not folder.is_dir():
        return None
    example = folder / "example.curriculum.json"
    if example.is_file():
        return example
    files = sorted(folder.glob("*.curriculum.json"))
    return files[0] if files else None


def programs_xml_for(curriculum: Path | None) -> Path | None:
    """The menu beside a curriculum, when the names match.

    ``street.curriculum.json`` uses ``street.xml``. If that file is
    missing and exactly one ``street.*.xml`` sits beside it, that is the menu.
    """
    if curriculum is None:
        return None
    suffix = ".curriculum.json"
    if not curriculum.name.endswith(suffix):
        return None
    stem = curriculum.name[: -len(suffix)]
    exact = curriculum.parent / f"{stem}.xml"
    if exact.is_file():
        return exact
    matches = sorted(
        path for path in curriculum.parent.glob(f"{stem}.*.xml") if path.is_file()
    )
    if len(matches) == 1:
        return matches[0]
    return None
