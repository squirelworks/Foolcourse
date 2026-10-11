"""Foolcourse catalog window.

Lists courses by subject and module. Selecting one launches Foolbook
with that book. Progress and scores come from the shared progress file.
The overall score counts only the official list of the curriculum.
Anything else is extra material.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    tk = None

from progress.progress import Progress, default_path
from main.catalog import official_ids, scan
from main.curriculum import apply, load as load_curriculum



def _find_foolbook() -> Path | None:
    """Locate foolbook.py. Sibling checkout, FOOLBOOK, or this tree."""
    import os
    env = os.environ.get("FOOLBOOK")
    if env:
        p = Path(env)
        if p.is_dir():
            p = p / "foolbook.py"
        if p.exists():
            return p
    here = Path(__file__).resolve().parents[1]
    candidates = [
        here / "foolbook.py",
        here.parent / "Foolbook" / "foolbook.py",
        here.parent / "foolbook" / "foolbook.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None



def _row_style(root):
    """Give list rows enough height for the font. The theme default clips them."""
    import tkinter.font as tkfont
    style = ttk.Style(root)
    font = tkfont.nametofont("TkDefaultFont")
    height = font.metrics("linespace") + 10
    style.configure("Treeview", rowheight=height, font=font)
    style.configure("Treeview.Heading", font=font, padding=(4, 6))

class Catalog:
    def __init__(self, root: Path, xml_path: Path | None = None, curriculum: Path | None = None, port: int = 1337):
        if tk is None:
            print("Tkinter is required for the Foolcourse window.")
            raise SystemExit(1)
        self.courses_root = Path(root)
        self.xml_path = Path(xml_path) if xml_path else None
        self.curriculum_path = Path(curriculum) if curriculum else None
        self.port = port
        self.curriculum: dict | None = None
        self.progress = Progress(default_path())
        self.catalog: dict = {"title": "Foolcourse", "subjects": []}
        self.rows: list[dict] = []

        self.root = tk.Tk()
        self.root.title("Foolcourse")
        self.root.geometry("1040x560")
        self.root.minsize(720, 360)
        _row_style(self.root)
        self._build()
        self._reload()
        self.root.mainloop()

    def _build(self):
        bar = ttk.Frame(self.root, padding=4)
        bar.pack(fill="x")
        ttk.Button(bar, text="Courses folder", command=self._pick_root).pack(side="left")
        ttk.Button(bar, text="courses.xml", command=self._pick_xml).pack(side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self._reload).pack(side="left", padx=4)

        info = ttk.Frame(self.root, padding=(4, 0, 4, 4))
        info.pack(fill="x")
        self.heading = ttk.Label(info, text="Foolcourse")
        self.heading.pack(side="left")
        self.overall = ttk.Label(info, text="")
        self.overall.pack(side="right")

        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        cols = ("subject", "module", "course", "id", "progress", "score", "track")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        # Weight is the share of spare width. Course gets the most so titles fit.
        self._col_weight = {
            "subject": 2, "module": 2, "course": 4,
            "id": 1, "progress": 1, "score": 1, "track": 1,
        }
        self._col_min = {
            "subject": 90, "module": 90, "course": 160,
            "id": 70, "progress": 72, "score": 56, "track": 64,
        }
        labels = {
            "subject": "Subject", "module": "Module", "course": "Course",
            "id": "Id", "progress": "Progress", "score": "Score", "track": "Track",
        }
        for key in cols:
            self.tree.heading(key, text=labels[key])
            self.tree.column(
                key,
                width=self._col_min[key],
                minwidth=self._col_min[key],
                stretch=True,
            )
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.bind("<Configure>", self._fit_columns)
        self.tree.bind("<Double-1>", lambda _e: self._launch())

        bot = ttk.Frame(self.root, padding=4)
        bot.pack(fill="x")
        ttk.Button(bot, text="Open in Foolbook", command=self._launch).pack(side="left")
        self.status = ttk.Label(bot, text="")
        self.status.pack(side="left", padx=12)

    def _fit_columns(self, _event=None):
        """Give each column a share of the visible width. Course gets the most."""
        width = self.tree.winfo_width()
        if width <= 1:
            return
        weights = self._col_weight
        mins = self._col_min
        total_w = sum(weights.values()) or 1
        spare = max(0, width - sum(mins.values()))
        for key, weight in weights.items():
            share = mins[key] + int(spare * weight / total_w)
            self.tree.column(key, width=share)

    def _pick_root(self):
        p = filedialog.askdirectory(title="Courses folder")
        if p:
            self.courses_root = Path(p)
            self._reload()

    def _pick_xml(self):
        p = filedialog.askopenfilename(
            title="courses.xml",
            filetypes=[("XML", "*.xml"), ("All", "*.*")],
        )
        if p:
            self.xml_path = Path(p)
            self._reload()

    def _reload(self):
        self.progress.reload()
        self.catalog = scan(self.courses_root, self.xml_path)
        if self.curriculum_path and self.curriculum_path.exists():
            self.curriculum = load_curriculum(self.curriculum_path)
            apply(self.catalog, self.curriculum)
        self._fill()

    def _fill(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows = []
        official = official_ids(self.catalog)
        for sub in self.catalog.get("subjects") or []:
            for mod in sub.get("modules") or []:
                for course in mod.get("courses") or []:
                    cid = course.get("id") or ""
                    is_off = bool(course.get("official"))
                    score = self.progress.course_score(cid)
                    best = score.get("best")
                    score_txt = ""
                    if best is not None:
                        answered = score.get("answered") or 0
                        correct = score.get("correct") or 0
                        score_txt = f"{best:.0f}%"
                        if answered:
                            score_txt += f" ({correct}/{answered})"
                    self.rows.append({
                        "id": cid,
                        "path": course.get("path") or "",
                        "official": is_off,
                    })
                    self.tree.insert("", "end", values=(
                        sub.get("name") or "",
                        mod.get("name") or "",
                        course.get("title") or cid,
                        cid,
                        self.progress.status(cid),
                        score_txt,
                        "official" if is_off else "",
                    ))
        ov = self.progress.overall(official)
        list_name = (
            (self.curriculum or {}).get("official_name")
            or self.catalog.get("official_name")
            or "Official"
        )
        if ov["percent"] is None:
            text = f"Overall ({list_name}): —   ({ov['official']} official)"
        else:
            text = (
                f"Overall ({list_name}): {ov['percent']:.0f}%"
                f"   ({ov['scored']} of {ov['official']} scored)"
            )
        if ov["excluded"]:
            text += f"   {ov['excluded']} other scored, not counted"
        self.overall.config(text=text)
        n = len(self.rows)
        root_name = self.courses_root.name or str(self.courses_root)
        self.status.config(text=f"{n} courses in {root_name}")
        self.heading.config(text=self.catalog.get("title") or "Foolcourse")

    def _selected(self) -> dict | None:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return self.rows[idx] if 0 <= idx < len(self.rows) else None

    def _launch(self):
        row = self._selected()
        if not row:
            messagebox.showinfo("Foolcourse", "Select a course first.")
            return
        path = row.get("path") or ""
        if not path or not Path(path).exists():
            messagebox.showwarning("Foolcourse", f"Course file not found:\n{path or '(no path)'}")
            return
        cid = row.get("id") or ""
        self.progress.touch(cid)
        self._fill()
        foolbook = _find_foolbook()
        if foolbook is None:
            messagebox.showwarning(
                "Foolcourse",
                "Foolbook was not found.\n"
                "Put Foolbook next to Foolcourse, or set FOOLBOOK.",
            )
            return
        cmd = [sys.executable, str(foolbook), "--port", str(self.port), path]
        subprocess.Popen(cmd)
