"""Foollege loader.

Own copy. Foolversity writes the file. Foolcourse does not import it.
A foollege owns courses. This filters a catalog to those courses.
"""

from __future__ import annotations

import json
from pathlib import Path


def load(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    data.setdefault("id", Path(path).stem.split(".")[0])
    data.setdefault("name", data["id"])
    data.setdefault("courses", [])
    return data


def apply(catalog: dict, foollege: dict) -> dict:
    """Keep only courses the foollege owns. Drop empty modules and subjects."""
    owned = {i for i in (foollege.get("courses") or []) if i}
    subjects = []
    for sub in catalog.get("subjects") or []:
        modules = []
        for mod in sub.get("modules") or []:
            courses = [c for c in (mod.get("courses") or []) if (c.get("id") or "") in owned]
            if courses:
                modules.append({**mod, "courses": courses})
        if modules:
            subjects.append({**sub, "modules": modules})
    catalog["subjects"] = subjects
    catalog["foollege"] = foollege.get("name") or foollege.get("id") or ""
    return catalog
