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

from foolcourse.progress.progress import Progress, default_path, student_path
from foolcourse.catalog import official_ids, scan
from foolcourse.locale import t
from foolcourse.curriculum import apply, load as load_curriculum



def _find_foolbook() -> Path | None:
    """Locate foolbook. Installed package, FOOLBOOK, or sibling checkout."""
    import os
    # Installed package
    try:
        import foolbook
        p = Path(foolbook.__file__).resolve()
        if p.name == "__init__.py":
            p = p.parent / "__main__.py"
        if p.exists():
            return p
    except ImportError:
        pass
    # Env override
    env = os.environ.get("FOOLBOOK")
    if env:
        p = Path(env)
        if p.is_dir():
            p = p / "foolbook.py"
        if p.exists():
            return p
    # Sibling checkout
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
    def __init__(self, root: Path, xml_path: Path | None = None, curriculum: Path | None = None, port: int = 1337, student: str | None = None, theme: str = "classic", locale: str = "en", debug: bool = False):
        if tk is None:
            print("Tkinter is required for the Foolcourse window.")
            raise SystemExit(1)
        self.courses_root = Path(root)
        self.xml_path = Path(xml_path) if xml_path else None
        self.curriculum_path = Path(curriculum) if curriculum else None
        self.port = port
        self._viewer = None
        self.debug = debug
        self.locale = locale or "en"
        self.curriculum: dict | None = None
        self.progress = Progress(student_path(student) if student else default_path())
        if not locale:
            self.locale = str(self.progress.data.get("locale") or "en")
        self.catalog: dict = {"title": "Foolcourse", "subjects": []}
        self.subject_i: int | None = None
        self.module_i: int | None = None
        self.course_rows: list[dict] = []
        self._filling = False

        self.root = tk.Tk()
        self.root.title(t(self.locale, "app"))
        self.root.geometry("1040x560")
        self.root.minsize(720, 360)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        _row_style(self.root)
        self._build()
        self._reload()
        self.root.bind("<FocusIn>", lambda _e: self._refresh_scores())
        self.root.mainloop()

    def _build(self):
        bar = ttk.Frame(self.root, padding=4)
        bar.pack(fill="x")
        ttk.Button(bar, text=t(self.locale, "courses_folder"), command=self._pick_root).pack(side="left")
        ttk.Button(bar, text=t(self.locale, "courses_xml"), command=self._pick_xml).pack(side="left", padx=4)
        ttk.Button(bar, text=t(self.locale, "refresh"), command=self._reload).pack(side="left", padx=4)

        info = ttk.Frame(self.root, padding=(4, 0, 4, 4))
        info.pack(fill="x")
        self.heading = ttk.Label(info, text=t(self.locale, "app"))
        self.heading.pack(side="left")
        self.crumb = ttk.Label(info, text="")
        self.crumb.pack(side="left", padx=12)
        self.overall = ttk.Label(info, text="")
        self.overall.pack(side="right")

        self.cols = ttk.Frame(self.root)
        self.cols.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.cols.rowconfigure(0, weight=1)

        self.sub_tree = self._list(self.cols, 0, t(self.locale, "subject"))
        self.mod_tree = self._list(self.cols, 1, t(self.locale, "module"))
        self.course_tree, self.course_frame = self._course_list(self.cols, 2)
        self.sub_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_subject())
        self.mod_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_module())
        self.course_tree.bind("<Double-1>", lambda _e: self._launch())

        bot = ttk.Frame(self.root, padding=4)
        bot.pack(fill="x")
        ttk.Button(bot, text=t(self.locale, "open"), command=self._launch).pack(side="left")
        self.status = ttk.Label(bot, text=t(self.locale, "select_subject"))
        self.status.pack(side="left", padx=12)

    def _list(self, parent, column: int, heading: str):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=("name",), show="headings", selectmode="browse")
        tree.heading("name", text=heading)
        tree.column("name", width=160, minwidth=80, stretch=True)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        frame.grid_remove()
        return tree

    def _course_list(self, parent, column: int):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        cols = ["course", "progress", "score"]
        if self.debug:
            cols += ["id", "track"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        labels = {
            "course": t(self.locale, "course"),
            "progress": t(self.locale, "progress"),
            "score": t(self.locale, "score"),
            "id": t(self.locale, "id"),
            "track": t(self.locale, "track"),
        }
        mins = {"course": 160, "progress": 72, "score": 72, "id": 80, "track": 72}
        for key in cols:
            tree.heading(key, text=labels[key])
            tree.column(key, width=mins[key], minwidth=mins[key], stretch=key == "course")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        frame.grid_remove()
        return tree, frame

    def _layout(self):
        """One column until a subject is chosen, then two, then three.

        Once a later column is open, the earlier columns stay narrow so
        the names truncate and the current list gets the width.
        """
        show_mod = self.subject_i is not None
        show_course = show_mod and self.module_i is not None
        sub_frame = self.sub_tree.master
        mod_frame = self.mod_tree.master
        sub_frame.grid()
        if show_mod:
            mod_frame.grid()
        else:
            mod_frame.grid_remove()
        if show_course:
            self.course_frame.grid()
        else:
            self.course_frame.grid_remove()
        for i in range(3):
            self.cols.columnconfigure(i, weight=0, minsize=0)
        if not show_mod:
            self.cols.columnconfigure(0, weight=1, minsize=200)
        elif not show_course:
            self.cols.columnconfigure(0, weight=0, minsize=140)
            self.cols.columnconfigure(1, weight=1, minsize=200)
        else:
            self.cols.columnconfigure(0, weight=0, minsize=120)
            self.cols.columnconfigure(1, weight=0, minsize=140)
            self.cols.columnconfigure(2, weight=1, minsize=240)

    def _pick_root(self):
        p = filedialog.askdirectory(title=t(self.locale, "courses_folder"))
        if p:
            self.courses_root = Path(p)
            self.subject_i = None
            self.module_i = None
            self._reload()

    def _pick_xml(self):
        p = filedialog.askopenfilename(
            title="courses.xml",
            filetypes=[("XML", "*.xml"), ("All", "*.*")],
        )
        if p:
            self.xml_path = Path(p)
            self.subject_i = None
            self.module_i = None
            self._reload()

    def _reload(self):
        self.progress.reload()
        self.catalog = scan(self.courses_root, self.xml_path)
        if self.curriculum_path and self.curriculum_path.exists():
            self.curriculum = load_curriculum(self.curriculum_path)
            apply(self.catalog, self.curriculum)
        subjects = self.catalog.get("subjects") or []
        if self.subject_i is not None and self.subject_i >= len(subjects):
            self.subject_i = None
            self.module_i = None
        if self.subject_i is not None:
            modules = subjects[self.subject_i].get("modules") or []
            if self.module_i is not None and self.module_i >= len(modules):
                self.module_i = None
        self._fill()

    def _refresh_scores(self):
        """Re-read progress when the window is focused again. Do not rescan."""
        self.progress.reload()
        self._fill_courses()
        self._overall()

    def _fill(self):
        if self._filling:
            return
        self._filling = True
        try:
            self._fill_subjects()
            self._fill_modules()
            self._fill_courses()
            self._layout()
            self._overall()
            self._crumb()
        finally:
            self._filling = False

    def _on_subject(self):
        if self._filling:
            return
        sel = self.sub_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx == self.subject_i:
            return
        self.subject_i = idx
        self.module_i = None
        self._fill()
        n = len((self.catalog["subjects"][idx].get("modules") or []))
        self.status.config(text=t(self.locale, "select_module", n=n))

    def _on_module(self):
        if self._filling:
            return
        sel = self.mod_tree.selection()
        if not sel or self.subject_i is None:
            return
        idx = int(sel[0])
        if idx == self.module_i:
            return
        self.module_i = idx
        self._fill()
        self.status.config(text=t(self.locale, "select_course", n=len(self.course_rows)))

    def _fill_subjects(self):
        tree = self.sub_tree
        for i in tree.get_children():
            tree.delete(i)
        narrow = self.subject_i is not None
        for i, sub in enumerate(self.catalog.get("subjects") or []):
            tree.insert("", "end", iid=str(i), values=(_clip(sub.get("name") or "", narrow),))
        if self.subject_i is not None:
            tree.selection_set(str(self.subject_i))
            tree.see(str(self.subject_i))

    def _fill_modules(self):
        tree = self.mod_tree
        for i in tree.get_children():
            tree.delete(i)
        if self.subject_i is None:
            return
        modules = (self.catalog["subjects"][self.subject_i].get("modules") or [])
        narrow = self.module_i is not None
        for i, mod in enumerate(modules):
            tree.insert("", "end", iid=str(i), values=(_clip(mod.get("name") or "", narrow),))
        if self.module_i is not None and str(self.module_i) in tree.get_children():
            tree.selection_set(str(self.module_i))
            tree.see(str(self.module_i))

    def _fill_courses(self):
        tree = self.course_tree
        keep = None
        sel = tree.selection()
        if sel and self.course_rows:
            idx = tree.index(sel[0])
            if 0 <= idx < len(self.course_rows):
                keep = self.course_rows[idx].get("id")
        for i in tree.get_children():
            tree.delete(i)
        self.course_rows = []
        if self.subject_i is None or self.module_i is None:
            return
        subject = self.catalog["subjects"][self.subject_i]
        module = (subject.get("modules") or [])[self.module_i]
        for course in module.get("courses") or []:
            cid = course.get("id") or ""
            self.course_rows.append({
                "id": cid,
                "path": course.get("path") or "",
                "official": bool(course.get("official")),
            })
            values = [
                course.get("title") or cid,
                _progress_label(self.progress, cid, self.locale),
                _score_text(self.progress, cid),
            ]
            if self.debug:
                values.append(cid)
                values.append(t(self.locale, "official") if course.get("official") else "")
            iid = tree.insert("", "end", values=tuple(values))
            if keep and cid == keep:
                tree.selection_set(iid)

    def _crumb(self):
        parts = []
        subjects = self.catalog.get("subjects") or []
        if self.subject_i is not None and self.subject_i < len(subjects):
            parts.append(subjects[self.subject_i].get("name") or "")
            modules = subjects[self.subject_i].get("modules") or []
            if self.module_i is not None and self.module_i < len(modules):
                parts.append(modules[self.module_i].get("name") or "")
        self.crumb.config(text=" / ".join(parts))
        if self.subject_i is None:
            self.status.config(text=t(self.locale, "select_subject"))

    def _overall(self):
        official = official_ids(self.catalog)
        ov = self.progress.overall(official)
        list_name = (
            (self.curriculum or {}).get("official_name")
            or self.catalog.get("official_name")
            or "Official"
        )
        if ov["percent"] is None:
            text = t(self.locale, "overall_empty", name=list_name, n=ov["official"])
        else:
            text = t(
                self.locale, "overall",
                name=list_name, pct=ov["percent"],
                scored=ov["scored"], n=ov["official"],
            )
        if ov["excluded"]:
            text += t(self.locale, "overall_other", n=ov["excluded"])
        self.overall.config(text=text)
        self.heading.config(text=self.catalog.get("title") or t(self.locale, "app"))

    def _selected(self) -> dict | None:
        sel = self.course_tree.selection()
        if not sel:
            return None
        idx = self.course_tree.index(sel[0])
        return self.course_rows[idx] if 0 <= idx < len(self.course_rows) else None


    def _port_free(self) -> bool:
        import socket
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", self.port))
            return True
        except OSError:
            return False
        finally:
            s.close()

    def _on_close(self):
        self._stop_viewer()
        self.root.destroy()

    def _stop_viewer(self) -> bool:
        """Stop the viewer we started. True if the port is free afterward."""
        proc = getattr(self, "_viewer", None)
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
                proc.wait(timeout=1)
        self._viewer = None
        for _ in range(30):
            if self._port_free():
                return True
            import time
            time.sleep(0.1)
        return self._port_free()

    def _start_course_server(self):
        """Foolcourse serves the current book. Foolbook fetches from here."""
        if not self._port_free():
            return True
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import json as _json
        from urllib.parse import urlparse, parse_qs

        catalog = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass
            def do_GET(self):
                u = urlparse(self.path)
                if u.path == "/api/book":
                    book = getattr(catalog, "_current_book", None)
                    if not book:
                        self.send_response(404)
                        self.end_headers()
                        return
                    body = _json.dumps(book).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif u.path == "/api/visit":
                    q = parse_qs(u.query)
                    page = (q.get("page") or [""])[0]
                    cid = (q.get("course") or [""])[0] or ""
                    if page and cid:
                        catalog.progress.mark_page(cid, page)
                    self.send_response(204)
                    self.end_headers()
                elif u.path == "/api/finish":
                    q = parse_qs(u.query)
                    cid = (q.get("course") or [""])[0]
                    if cid:
                        catalog.progress.complete(cid)
                    body = b'{"ok":true}'
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif u.path == "/api/current":
                    body = _json.dumps({"path": getattr(catalog, "_current_path", "")}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

        try:
            self._course_httpd = ThreadingHTTPServer(("127.0.0.1", self.port), H)
        except OSError:
            return False
        import threading
        threading.Thread(target=self._course_httpd.serve_forever, daemon=True).start()
        return True

    def _launch(self):
        row = self._selected()
        if not row:
            messagebox.showinfo(t(self.locale, "app"), t(self.locale, "select_first"))
            return
        path = row.get("path") or ""
        if not path or not Path(path).exists():
            messagebox.showwarning(t(self.locale, "app"), t(self.locale, "not_found", path=path or "(no path)"))
            return
        cid = row.get("id") or ""
        # Load the book and publish it
        try:
            from engine.loader import load
            from viewer.gui import book_to_json
            book = load(path)
            self._current_book = book_to_json(book, self.progress, cid)
            self._current_path = path
        except Exception as e:
            messagebox.showwarning(t(self.locale, "app"), f"Could not load: {e}")
            return
        if not self._start_course_server():
            messagebox.showinfo(t(self.locale, "app"), "Could not start the course server.")
            return
        foolbook = _find_foolbook()
        if foolbook is None:
            messagebox.showwarning(t(self.locale, "app"), t(self.locale, "no_foolbook"))
            return
        # Tell Foolbook to fetch from the course server
        url = f"http://127.0.0.1:{self.port}/"
        cmd = [sys.executable, str(foolbook), "--from", url, "--course", cid]
        # Replace any running viewer so the new book loads
        if self._viewer and self._viewer.poll() is None:
            self._viewer.terminate()
            try:
                self._viewer.wait(timeout=2)
            except Exception:
                self._viewer.kill()
        self._viewer = subprocess.Popen(cmd)
        self.progress.touch(cid)
        self._fill_courses()
        self.status.config(text=f"Course at {url}")



def _progress_label(progress: Progress, cid: str, locale: str) -> str:
    rec_label = progress.label(cid)
    if rec_label == "done":
        return t(locale, "done")
    if rec_label == "started":
        return t(locale, "started")
    if rec_label.endswith(" pages"):
        n = rec_label.split()[0]
        return t(locale, "pages", n=n)
    return rec_label


def _clip(text: str, narrow: bool) -> str:
    if not narrow or len(text) <= 18:
        return text
    return text[:17] + "…"


def _score_text(progress: Progress, cid: str) -> str:
    score = progress.course_score(cid)
    best = score.get("best")
    if best is None:
        return ""
    text = f"{best:.0f}%"
    answered = score.get("answered") or 0
    if answered:
        text += f" ({score.get('correct') or 0}/{answered})"
    return text

