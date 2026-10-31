"""Build a course catalog from a directory, optionally with a menu.

A deployment has an official course list. A course on that list counts
toward the overall score. Anything else is extra material: it is listed,
it can be opened, and it keeps its own score, but it is not added into
the overall.

The list is a curriculum file. A folder name does not decide it, and a
menu does not decide it. The menu supplies subjects, modules, and titles.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

BOOK_EXTS = {".tbk", ".fbk", ".fsk"}
_TITLE = re.compile(r'"title"\s*:\s*"((?:\\.|[^"\\])*)"')


def scan(root: Path, xml_path: Path | None = None) -> dict:
    """Return a catalog dict.

    With an xml path the hierarchy and titles come from the menu
    and files are matched by lesson id. Without one, the folder tree is
    the catalog. Nothing is official until a curriculum file says so.
    """
    root = Path(root)
    if xml_path and Path(xml_path).exists():
        return _from_xml(root, Path(xml_path))
    return _from_folders(root)



def _book_title(path: Path) -> str:
    """Title from the front of a book. Do not unpack the pictures."""
    try:
        suffix = path.suffix.lower()
        if suffix == ".json":
            return _title_in(_head_text(path, 65536))
        if suffix != ".fbk":
            return ""
        twin = path.with_suffix(".json")
        if twin.is_file() and twin.stat().st_size <= 65536:
            return _title_in(_head_text(twin, 65536))
        with path.open("rb") as handle:
            blob = handle.read(65536)
        if len(blob) < 5 or blob[:4] != b"FBK1":
            return ""
        payload = blob[5:]
        if blob[4] & 1:
            payload = zlib.decompressobj().decompress(payload, 16384)
        else:
            payload = payload[:16384]
        return _title_in(payload.decode("utf-8", "replace"))
    except Exception:
        return ""


def _head_text(path: Path, limit: int) -> str:
    with path.open("rb") as handle:
        return handle.read(limit).decode("utf-8", "replace")


def _title_in(text: str) -> str:
    match = _TITLE.search(text)
    if not match:
        return ""
    try:
        return str(json.loads('"' + match.group(1) + '"'))
    except ValueError:
        return ""


def official_ids(catalog: dict) -> set[str]:
    ids: set[str] = set()
    for sub in catalog.get("subjects") or []:
        for mod in sub.get("modules") or []:
            for course in mod.get("courses") or []:
                if course.get("official"):
                    cid = course.get("id") or ""
                    if cid:
                        ids.add(cid)
    return ids


def _from_folders(root: Path) -> dict:
    tree: dict[str, dict[str, list[dict]]] = {}
    if not root.exists():
        return {"title": "Foolcourse", "root": str(root), "subjects": []}
    listings: dict[Path, dict[str, dict]] = {}
    for book in sorted(root.rglob("*")):
        if not book.is_file() or book.suffix.lower() not in BOOK_EXTS:
            continue
        if book.name.startswith("."):
            continue
        # A .json next to an .fbk is the working copy. List the book once.
        if book.suffix.lower() == ".json" and book.with_suffix(".fbk").exists():
            continue
        # A .tbk next to an .fbk or .json is the legacy copy. List the book once.
        if book.suffix.lower() == ".tbk":
            if book.with_suffix(".fbk").exists() or book.with_suffix(".json").exists():
                continue
        # <stem>.<locale>.json is an overlay, not a course.
        if book.suffix.lower() == ".json" and "." in book.stem:
            continue
        rel = book.relative_to(root)
        parts = list(rel.parts)
        # subject / module / book, or module / book, or just book
        folders = parts[:-1]
        if len(folders) >= 2:
            subject, module = folders[0], folders[1]
        elif len(folders) == 1:
            subject, module = folders[0], folders[0]
        else:
            subject, module = "Courses", "Courses"
        course_id = book.stem
        listed = _listed(book.parent, listings).get(book.name) or {}
        title = str(listed.get("title") or "") or _book_title(book) or course_id
        course = {
            "id": course_id,
            "title": title,
            "path": str(book),
            "official": False,
        }
        if isinstance(listed.get("pages"), int):
            course["pages"] = listed["pages"]
        tree.setdefault(subject, {}).setdefault(module, []).append(course)
    return _pack(root, tree)


def _listed(folder: Path, listings: dict) -> dict[str, dict]:
    """The folder's books.json, by file name. A published folder carries one.

    It names each book's title, file, and page count. A folder without one,
    or with one that does not read, is listed from the books themselves.
    """
    if folder not in listings:
        books = {}
        try:
            data = json.loads((folder / "books.json").read_text(encoding="utf-8"))
            for entry in data.get("books") or []:
                if isinstance(entry, dict) and entry.get("file"):
                    books[str(entry["file"])] = entry
        except (OSError, ValueError, AttributeError):
            pass
        listings[folder] = books
    return listings[folder]


def _from_xml(root: Path, xml_path: Path) -> dict:
    files = _index_books(root)
    tree = ET.parse(xml_path)
    doc = tree.getroot()
    subjects = []
    seen: set[str] = set()
    for menu in doc.findall("Menu"):
        courseid = menu.get("courseid") or ""
        title = menu.get("title") or courseid or "Courses"
        modules = _modules(menu, files, seen)
        if modules:
            subjects.append({
                "name": title,
                "official": False,
                "modules": modules,
            })
    # Books on disk that the menu does not name. Not official.
    extras = []
    for key, path in sorted(files.items()):
        if key in seen:
            continue
        extras.append({
            "id": Path(path).stem,
            "title": Path(path).stem,
            "path": path,
            "official": False,
        })
    if extras:
        subjects.append({
            "name": "Uncatalogued",
            "official": False,
            "modules": [{"name": "On disk", "courses": extras}],
        })
    return {
        "title": "Foolcourse",
        "root": str(root),
        "xml": str(xml_path),
        "subjects": subjects,
    }


def _modules(menu, files: dict, seen: set[str]) -> list[dict]:
    """Modules under one subject.

    A menu three levels deep keeps the unit. The module name is
    "group / unit", so the third level is not folded into the group.
    """
    modules = []

    def add(name: str, node) -> None:
        courses = []
        for item in node.findall("Item"):
            lid = item.get("lessonid") or ""
            if not lid:
                continue
            path = files.get(lid.lower()) or files.get(lid)
            courses.append({
                "id": lid,
                "title": item.get("title") or lid,
                "path": path or "",
                "official": False,
            })
            seen.add(lid.lower())
        if courses:
            modules.append({"name": name, "courses": courses})

    def walk(node, prefix: str) -> None:
        title = node.get("title") or "Module"
        name = f"{prefix} / {title}" if prefix else title
        add(name, node)
        for child in node.findall("Menu"):
            walk(child, name)

    for child in menu.findall("Menu"):
        walk(child, "")
    add(menu.get("title") or "Courses", menu)
    return modules


def _index_books(root: Path) -> dict[str, str]:
    """Map lowercased stem to the first matching book path."""
    found: dict[str, str] = {}
    if not root.exists():
        return found
    for book in root.rglob("*"):
        if not book.is_file() or book.suffix.lower() not in BOOK_EXTS:
            continue
        key = book.stem.lower()
        found.setdefault(key, str(book))
    return found


def _pack(root: Path, tree: dict[str, dict[str, list[dict]]]) -> dict:
    subjects = []
    for subject, modules in tree.items():
        official = any(
            c.get("official")
            for courses in modules.values()
            for c in courses
        )
        subjects.append({
            "name": subject,
            "official": official,
            "modules": [
                {"name": mod, "courses": courses}
                for mod, courses in modules.items()
            ],
        })
    return {"title": "Foolcourse", "root": str(root), "subjects": subjects}
