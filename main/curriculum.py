"""Curriculum maker.

A curriculum is a named official course list plus extra material.
Anything not on the official list is extra: catalogued, openable, and
scored on its own, but not counted in the overall.

ATT is one curriculum. Its official list is ATT Master. A later
deployment makes its own file and does not need ATT names.

File shape:

    {
      "name": "ATT",
      "official_name": "ATT Master",
      "official": ["93951100", "93951101"],
      "extras": ["sidequest"],
      "root": "courses/",
      "notes": ""
    }

extras may be omitted. Anything not in official is extra either way.
"""

from __future__ import annotations

import json
from pathlib import Path

from main.catalog import official_ids, scan


def load(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("curriculum file is not an object")
    data.setdefault("name", Path(path).stem)
    data.setdefault("official_name", data["name"])
    data["official"] = [str(i) for i in (data.get("official") or []) if i]
    data["extras"] = [str(i) for i in (data.get("extras") or []) if i]
    return data


def save(path: Path, curriculum: dict) -> Path:
    path = Path(path)
    body = {
        "name": curriculum.get("name") or path.stem,
        "official_name": curriculum.get("official_name") or curriculum.get("name") or path.stem,
        "official": list(curriculum.get("official") or []),
        "extras": list(curriculum.get("extras") or []),
        "root": curriculum.get("root") or "",
        "notes": curriculum.get("notes") or "",
    }
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return path


def from_catalog(catalog: dict, name: str, official_name: str = "") -> dict:
    """Build a curriculum from a catalog's current official flags."""
    official = sorted(official_ids(catalog))
    all_ids = _all_ids(catalog)
    extras = sorted(i for i in all_ids if i not in set(official))
    return {
        "name": name,
        "official_name": official_name or name,
        "official": official,
        "extras": extras,
        "root": catalog.get("root") or "",
        "notes": "",
    }


def apply(catalog: dict, curriculum: dict) -> dict:
    """Mark official from the curriculum. Everything else becomes extra.

    The catalog's title and official_name are set from the curriculum so
    the window can label the overall by the list, not by a fixed name.
    """
    official = {i for i in (curriculum.get("official") or []) if i}
    for sub in catalog.get("subjects") or []:
        any_off = False
        for mod in sub.get("modules") or []:
            for course in mod.get("courses") or []:
                on = (course.get("id") or "") in official
                course["official"] = on
                if on:
                    any_off = True
        sub["official"] = any_off
    catalog["title"] = curriculum.get("name") or catalog.get("title") or "Foolcourse"
    catalog["official_name"] = curriculum.get("official_name") or catalog["title"]
    catalog["curriculum"] = curriculum.get("name") or ""
    return catalog


def _all_ids(catalog: dict) -> set[str]:
    ids: set[str] = set()
    for sub in catalog.get("subjects") or []:
        for mod in sub.get("modules") or []:
            for course in mod.get("courses") or []:
                cid = course.get("id") or ""
                if cid:
                    ids.add(cid)
    return ids


class Maker:
    """Window to mark courses official or extra and save a curriculum."""

    def __init__(self, root: Path, xml_path: Path | None = None, out: Path | None = None):
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox, simpledialog
        except ImportError:
            print("Tkinter is required for the curriculum maker.")
            raise SystemExit(1)
        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.simpledialog = simpledialog

        self.courses_root = Path(root)
        self.xml_path = Path(xml_path) if xml_path else None
        self.out = Path(out) if out else self.courses_root / "curriculum.json"
        self.catalog = scan(self.courses_root, self.xml_path)
        self.rows: list[dict] = []

        self.root = tk.Tk()
        self.root.title("Curriculum maker")
        self.root.geometry("980x560")
        self._build()
        self._fill()
        self.root.mainloop()

    def _build(self):
        tk, ttk = self.tk, self.ttk
        bar = ttk.Frame(self.root, padding=4)
        bar.pack(fill="x")
        ttk.Label(bar, text="Curriculum").pack(side="left")
        self.name = ttk.Entry(bar, width=24)
        self.name.insert(0, "Curriculum")
        self.name.pack(side="left", padx=4)
        ttk.Label(bar, text="Official list").pack(side="left", padx=(12, 0))
        self.official_name = ttk.Entry(bar, width=24)
        self.official_name.insert(0, "Official")
        self.official_name.pack(side="left", padx=4)
        ttk.Button(bar, text="Save", command=self._save).pack(side="right")

        cols = ("subject", "module", "course", "id", "role")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="extended")
        for key, label, width in (
            ("subject", "Subject", 180),
            ("module", "Module", 200),
            ("course", "Course", 280),
            ("id", "Id", 120),
            ("role", "Role", 90),
        ):
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width)
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        bot = ttk.Frame(self.root, padding=4)
        bot.pack(fill="x")
        ttk.Button(bot, text="Mark official", command=lambda: self._set(True)).pack(side="left")
        ttk.Button(bot, text="Mark extra", command=lambda: self._set(False)).pack(side="left", padx=4)
        self.status = ttk.Label(bot, text="")
        self.status.pack(side="left", padx=12)

    def _fill(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows = []
        for sub in self.catalog.get("subjects") or []:
            for mod in sub.get("modules") or []:
                for course in mod.get("courses") or []:
                    self.rows.append(course)
                    self.tree.insert("", "end", values=(
                        sub.get("name") or "",
                        mod.get("name") or "",
                        course.get("title") or course.get("id") or "",
                        course.get("id") or "",
                        "official" if course.get("official") else "extra",
                    ))
        self._count()

    def _set(self, official: bool):
        sel = self.tree.selection()
        if not sel:
            return
        for item in sel:
            idx = self.tree.index(item)
            if 0 <= idx < len(self.rows):
                self.rows[idx]["official"] = official
        self._fill()

    def _count(self):
        off = sum(1 for c in self.rows if c.get("official"))
        self.status.config(text=f"{off} official, {len(self.rows) - off} extra")

    def _save(self):
        name = self.name.get().strip() or "Curriculum"
        official_name = self.official_name.get().strip() or name
        curriculum = from_catalog(self.catalog, name, official_name)
        path = save(self.out, curriculum)
        self.messagebox.showinfo(
            "Curriculum maker",
            f"Saved {path.name}\n{len(curriculum['official'])} official, "
            f"{len(curriculum['extras'])} extra",
        )
