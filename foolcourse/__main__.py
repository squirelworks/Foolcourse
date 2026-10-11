"""Foolcourse entry.

  python3 -m foolcourse                         # catalog _courses/
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

from foolcourse.catalog import official_ids, scan
from foolcourse.curriculum import apply, load as load_curriculum
from progress.progress import Progress, default_path


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    listing = False
    making = False
    xml_path = None
    curriculum_path = None
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
        else:
            rest.append(a)
        i += 1

    root = Path(rest[0]) if rest else _default_root()
    if making:
        from foolcourse.curriculum import Maker
        out = Path(rest[1]) if len(rest) > 1 else root / "curriculum.json"
        Maker(root, xml_path, out)
        return 0
    catalog = scan(root, xml_path)
    curriculum = None
    if curriculum_path and curriculum_path.exists():
        curriculum = load_curriculum(curriculum_path)
        apply(catalog, curriculum)
    if listing:
        return _print(catalog, curriculum)
    from foolcourse.ui import Catalog
    Catalog(root, xml_path, curriculum_path)
    return 0


def _default_root() -> Path:
    here = Path(__file__).resolve().parents[1]
    for name in ("courses", "_courses"):
        p = here / name
        if p.exists():
            return p
    return here / "_courses"


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
