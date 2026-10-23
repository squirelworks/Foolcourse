"""Where a Foolcourse install keeps its own files.

The curriculum ships with the program. The courses do not. A portable
copy, the kind you unzip on Windows, remembers the folder you point it at.
"""

from __future__ import annotations

import os
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

    The portable app asks the first time. A source checkout uses its own
    _courses folder and does not ask.
    """
    if given is not None:
        folder = given.expanduser()
        if folder.is_dir():
            remember_courses(folder)
        return folder
    saved = remembered_courses()
    if saved is not None:
        return saved
    if portable() and ask:
        chosen = ask_courses()
        if chosen is not None:
            remember_courses(chosen)
            return chosen
    if portable():
        return app_dir() / "_courses"
    return dev_courses_root()


def default_curriculum() -> Path | None:
    """The curriculum that belongs to this copy of the program.

    A portable copy loads the NIDA list that was packed beside it.
    A source checkout still prefers the small example.
    """
    folder = curriculum_dir()
    if not folder.is_dir():
        return None
    nida = folder / "nida.curriculum.json"
    if portable() and nida.is_file():
        return nida
    example = folder / "example.curriculum.json"
    if example.is_file():
        return example
    files = sorted(folder.glob("*.curriculum.json"))
    return files[0] if files else None


def programs_xml_for(curriculum: Path | None) -> Path | None:
    """The menu that goes with the NIDA curriculum, if this copy has it."""
    if curriculum is None:
        return None
    xml = curriculum.parent / "nida.programs.xml"
    if curriculum.name.startswith("nida.") and xml.is_file():
        return xml
    return None
