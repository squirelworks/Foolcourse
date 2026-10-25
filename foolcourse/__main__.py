"""Foolcourse entry.

  python3 -m foolcourse                         # _courses/ with _curriculum/
  python3 -m foolcourse path/to/courses         # catalog that folder
  python3 -m foolcourse path/to/courses --xml courses.xml
  python3 -m foolcourse --list path/to/courses  # print, no window
  python3 -m foolcourse --debug                 # show course id and track
  python3 -m foolcourse --theme modern          # quieter controls, not Win95
  python3 -m foolcourse --student alex          # _student/alex.fcs
  python3 -m foolcourse --locale klingon        # Foolcourse strings; course text stays
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from foolcourse.catalog import official_ids, scan
from foolcourse.curriculum import apply, load as load_curriculum
from foolcourse.home import default_curriculum, programs_xml_for, resolve_courses
from foolcourse.progress.progress import Progress, default_path, student_path


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if "--freshstart" in argv:
        return _freshstart()
    if "--doctor" in argv:
        from foolcourse._debug.dump import dump
        path = dump("doctor")
        print(f"Wrote {path}")
        return 0
    listing = False
    making = False
    debug = False
    xml_path = None
    curriculum_path = None
    port = 1337
    theme = "classic"
    student = None
    locale = None
    port_set = False
    rest: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--list":
            listing = True
        elif a == "--make":
            making = True
        elif a == "--debug":
            debug = True
        elif a == "--xml" and i + 1 < len(argv):
            xml_path = Path(argv[i + 1])
            i += 1
        elif a == "--curriculum" and i + 1 < len(argv):
            curriculum_path = Path(argv[i + 1])
            i += 1
        elif a == "--theme" and i + 1 < len(argv):
            theme = argv[i + 1].strip().lower()
            if theme not in ("classic", "modern"):
                print("--theme is classic or modern")
                return 2
            i += 1
        elif a == "--student" and i + 1 < len(argv):
            student = argv[i + 1]
            i += 1
        elif a == "--locale" and i + 1 < len(argv):
            locale = argv[i + 1]
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
            port_set = True
            i += 1
        else:
            rest.append(a)
        i += 1

    given = Path(rest[0]) if rest else None
    if curriculum_path is None:
        curriculum_path = default_curriculum()
    if xml_path is None:
        xml_path = programs_xml_for(curriculum_path)
    root = resolve_courses(given, ask=not listing and not making)
    if making:
        from foolcourse.curriculum import Maker
        out = Path(rest[1]) if len(rest) > 1 else _curriculum_dir() / "curriculum.json"
        Maker(root, xml_path, out, theme=theme)
        return 0
    catalog = scan(root, xml_path)
    curriculum = None
    if curriculum_path and curriculum_path.exists():
        curriculum = load_curriculum(curriculum_path)
        apply(catalog, curriculum)
    from foolcourse.locale import resolve
    progress = Progress(student_path(student) if student else default_path())
    if locale is None:
        locale = str(progress.data.get("locale") or "en")
    locale = resolve(locale)
    if locale != (progress.data.get("locale") or "en"):
        progress.set_locale(locale)
    if theme == "classic" and progress.data.get("theme"):
        theme = str(progress.data["theme"])
    if not port_set and progress.data.get("port"):
        port = int(progress.data["port"])
    if listing:
        return _print(catalog, curriculum, debug=debug, student=student)
    from foolcourse.ui import Catalog
    Catalog(root, xml_path, curriculum_path, port, student, theme, locale, debug)
    return 0


def _freshstart() -> int:
    """Force-reinstall Foolcourse and everything under it."""
    import subprocess
    cmd = [
        sys.executable, "-m", "pip", "install", "--force-reinstall",
        "git+https://github.com/squirelworks/Foolcourse.git@v1.0.0r7",
    ]
    return subprocess.call(cmd)


def _here() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_root() -> Path:
    # Shipped with the package
    pkg = Path(__file__).resolve().parent / "_courses"
    if pkg.exists():
        return pkg
    # Sibling checkout
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


def _print(catalog: dict, curriculum: dict | None = None, debug: bool = False, student: str | None = None) -> int:
    progress = Progress(student_path(student) if student else default_path())
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
                line = (
                    f"{sub.get('name','')} / {mod.get('name','')} / "
                    f"{course.get('title') or cid}  "
                    f"{progress.label(cid) or '-'}  {score_txt}"
                )
                if debug:
                    track = "official" if course.get("official") else ""
                    line += f"  [{cid}]  {track}"
                print(line)
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
