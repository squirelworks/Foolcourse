"""Build a course catalog from a directory, optionally with courses.xml.

A deployment has an official course list. A course on that list counts
toward the overall score. Anything else is extra material: it is listed,
it can be opened, and it keeps its own score, but it is not added into
the overall.

ATT is the first official list. A course is on it when either:

- it lives under a folder named 03_ATT_Master (or an alias), or
- its lesson id is in the ATT Master menu of a courses.xml
  (courseid 0_MASTER3 / title ATT Master_3).

A later deployment names its own list. The rule does not change.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

BOOK_EXTS = {".tbk", ".fbk", ".json", ".fsk"}

# Folder names that mark the official track. Compared case-insensitively
# after replacing spaces with underscores.
OFFICIAL_FOLDERS = {
    "03_att_master",
    "03_att_master_3",
    "att_master",
    "att_master_3",
    "0_master3",
    "master3",
}

# courses.xml menu that is the official track.
OFFICIAL_COURSEIDS = {"0_master3"}
OFFICIAL_TITLES = {"att master_3", "att master", "03_att_master"}


def _norm(name: str) -> str:
    return (name or "").strip().lower().replace(" ", "_").replace("-", "_")


def is_official_folder(name: str) -> bool:
    return _norm(name) in OFFICIAL_FOLDERS


def scan(root: Path, xml_path: Path | None = None) -> dict:
    """Return a catalog dict.

    With an xml path the hierarchy and titles come from the menu export
    and files are matched by lesson id. Without one, the folder tree is
    the catalog and a folder named 03_ATT_Master marks the official track.
    """
    root = Path(root)
    if xml_path and Path(xml_path).exists():
        return _from_xml(root, Path(xml_path))
    return _from_folders(root)



def _book_title(path: Path) -> str:
    """Title from a sibling .json or an .fbk envelope. Empty if unreadable."""
    import json, zlib
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".fbk":
            twin = path.with_suffix(".json")
            if twin.exists():
                data = json.loads(twin.read_text(encoding="utf-8"))
            else:
                blob = path.read_bytes()
                if blob[:4] != b"FBK1":
                    return ""
                payload = blob[5:]
                if blob[4] & 1:
                    payload = zlib.decompress(payload)
                data = json.loads(payload.decode("utf-8"))
        else:
            return ""
    except Exception:
        return ""
    return str(data.get("title") or "")


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
        official = any(is_official_folder(p) for p in folders)
        if len(folders) >= 2:
            subject, module = folders[0], folders[1]
        elif len(folders) == 1:
            subject, module = folders[0], folders[0]
        else:
            subject, module = "Courses", "Courses"
        course_id = book.stem
        title = _book_title(book) or course_id
        tree.setdefault(subject, {}).setdefault(module, []).append({
            "id": course_id,
            "title": title,
            "path": str(book),
            "official": official,
        })
    return _pack(root, tree)


def _from_xml(root: Path, xml_path: Path) -> dict:
    files = _index_books(root)
    tree = ET.parse(xml_path)
    doc = tree.getroot()
    subjects = []
    seen: set[str] = set()
    for menu in doc.findall("Menu"):
        courseid = menu.get("courseid") or ""
        title = menu.get("title") or courseid or "Courses"
        official_track = (
            _norm(courseid) in OFFICIAL_COURSEIDS
            or _norm(title) in OFFICIAL_TITLES
            or is_official_folder(title)
        )
        modules = _modules(menu, files, official_track, seen)
        if modules:
            subjects.append({
                "name": title,
                "official": official_track,
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


def _modules(menu, files: dict, official: bool, seen: set[str]) -> list[dict]:
    """Modules under one program.

    The NIDA list is three menus deep: program, group, unit. A unit that
    holds lessons becomes its own module, named "group / unit", so the
    third level is not folded into the group and lost.
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
                "official": official,
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
        official = is_official_folder(subject) or any(
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
