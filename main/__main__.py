"""Foolcourse entry.

  python3 -m foolcourse                         # _courses/ with _curriculum/
  python3 -m foolcourse path/to/courses         # catalog that folder
  python3 -m foolcourse path/to/courses --xml courses.xml
  python3 -m foolcourse --list path/to/courses  # print, no window
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from main.catalog import official_ids, scan
from main.curriculum import apply, load as load_curriculum
from progress.progress import Progress, default_path


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    listing = False
    making = False
    xml_path = None
    curriculum_path = None
    port = 1337
    rest: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--list":
            listing = True
        elif a == "--make":
            making = True
        elif a == "--xml" and i + 1 < len(argv):
            xml_path = Path(argv[i + 1])
            i += 1
        elif a == "--curriculum" and i + 1 < len(argv):
            curriculum_path = Path(argv[i + 1])
            i += 1
        elif a == "--port" and i + 1 < len(argv):
            try:
                port = int(argv[i + 1])
            except ValueError:
                print(f"--port needs a number, got {argv[i + 1]}")
                return 2
            if not 1 <= port <= 65535:
                print(f"--port out of range: {port}")
                return 2
            i += 1
        else:
            rest.append(a)
        i += 1

    root = Path(rest[0]) if rest else _default_root()
    if curriculum_path is None:
        curriculum_path = _default_curriculum()
    if making:
        from main.curriculum import Maker
        out = Path(rest[1]) if len(rest) > 1 else _curriculum_dir() / "curriculum.json"
        Maker(root, xml_path, out)
        return 0
    catalog = scan(root, xml_path)
    curriculum = None
    if curriculum_path and curriculum_path.exists():
        curriculum = load_curriculum(curriculum_path)
        apply(catalog, curriculum)
    if listing:
        return _print(catalog, curriculum)
    from main.ui import Catalog
    Catalog(root, xml_path, curriculum_path, port)
    return 0


def _here() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_root() -> Path:
    here = _here()
    for name in ("_courses", "courses"):
        p = here / name
        if p.exists():
            return p
    return here / "_courses"


def _curriculum_dir() -> Path:
    return _here() / "_curriculum"


def _default_curriculum() -> Path | None:
    """The default curriculum lives in _curriculum/.

    Prefer example.curriculum.json, then the first curriculum file.
    """
    folder = _curriculum_dir()
    if not folder.is_dir():
        return None
    preferred = folder / "example.curriculum.json"
    if preferred.exists():
        return preferred
    files = sorted(folder.glob("*.curriculum.json")) or sorted(folder.glob("*.json"))
    return files[0] if files else None


def _print(catalog: dict, curriculum: dict | None = None) -> int:
    progress = Progress(default_path())
    official = official_ids(catalog)
    n = 0
    for sub in catalog.get("subjects") or []:
        for mod in sub.get("modules") or []:
            for course in mod.get("courses") or []:
                n += 1
                cid = course.get("id") or ""
                score = progress.course_score(cid)
                best = score.get("best")
                score_txt = f"{best:.0f}%" if best is not None else "-"
                track = "official" if course.get("official") else ""
                print(
                    f"{sub.get('name','')} / {mod.get('name','')} / "
                    f"{course.get('title') or cid}  [{cid}]  "
                    f"{progress.status(cid) or '-'}  {score_txt}  {track}"
                )
    ov = progress.overall(official)
    list_name = (curriculum or {}).get("official_name") or catalog.get("official_name") or "Official"
    pct = f"{ov['percent']:.0f}%" if ov["percent"] is not None else "-"
    print(f"\n{n} courses")
    print(
        f"Overall ({list_name}): {pct}  "
        f"({ov['scored']} of {ov['official']} scored, "
        f"{ov['excluded']} other scored not counted)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
