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
from foolcourse.home import remember_courses, load_window, remember_window, fit_geometry, screen_geometry, portable



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


def _foolbook_cmd(book: str, course: str, student: str) -> list[str] | None:
    """Start Foolbook with this same interpreter.

    A portable Windows copy has Foolbook on PYTHONPATH, so -m foolbook
    works. A source checkout falls back to the file beside this program.
    """
    tail = [book, "--course", course, "--student", student]
    try:
        import foolbook  # noqa: F401
        return [sys.executable, "-m", "foolbook", *tail]
    except ImportError:
        found = _find_foolbook()
        if found is None:
            return None
        return [sys.executable, str(found), *tail]


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
        self.root.minsize(900, 420)
        saved = load_window()
        self._sash_memory = saved["sashes"]
        self._saved_zoom = saved["zoomed"]
        self._normal_geometry = saved["geometry"] or None
        self._ui_ready = False
        self._restoring = False
        self._save_after = None
        self._apply_geometry()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Configure>", self._on_configure)
        _row_style(self.root)
        self._build()
        self._reload()
        self.root.bind("<FocusIn>", lambda _e: self._refresh_scores())
        self.root.after_idle(self._finish_open)
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

        self.panes = ttk.Panedwindow(self.root, orient="horizontal")
        self.panes.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.panes.bind("<ButtonRelease-1>", self._on_sash)
        self._shown = None

        self.sub_tree, self.sub_frame = self._list(self.panes, t(self.locale, "subject"))
        self.mod_tree, self.mod_frame = self._list(self.panes, t(self.locale, "module"))
        self.course_tree, self.course_frame = self._course_list(self.panes)
        self.sub_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_subject())
        self.mod_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_module())
        self.course_tree.bind("<Double-1>", lambda _e: self._launch())

        bot = ttk.Frame(self.root, padding=4)
        bot.pack(fill="x")
        ttk.Button(bot, text=t(self.locale, "open"), command=self._launch).pack(side="left")
        self.status = ttk.Label(bot, text=t(self.locale, "select_subject"))
        self.status.pack(side="left", padx=12)

    def _list(self, parent, heading: str):
        frame = ttk.Frame(parent)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=("name",), show="headings", selectmode="browse")
        tree.heading("name", text=heading)
        tree.column("#0", width=0, minwidth=0, stretch=False)
        tree.column("name", width=320, minwidth=80, stretch=True)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        tree.bind("<Configure>", lambda event, tree=tree: self._fit_name(tree, event))
        return tree, frame

    def _course_list(self, parent):
        frame = ttk.Frame(parent)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        cols = ["course", "progress", "score"]
        if self.debug:
            cols += ["id", "track"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        tree.column("#0", width=0, minwidth=0, stretch=False)
        labels = {
            "course": t(self.locale, "course"),
            "progress": t(self.locale, "progress"),
            "score": t(self.locale, "score"),
            "id": t(self.locale, "id"),
            "track": t(self.locale, "track"),
        }
        widths = {"course": 420, "progress": 88, "score": 96, "id": 96, "track": 80}
        mins = {"course": 180, "progress": 72, "score": 72, "id": 80, "track": 72}
        for key in cols:
            tree.heading(key, text=labels[key])
            tree.column(key, width=widths[key], minwidth=mins[key], stretch=key == "course")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        tree.bind("<Configure>", lambda event, tree=tree: self._fit_course(tree, event))
        return tree, frame

    def _fit_name(self, tree, event):
        """The one column fills the pane, so dragging the divider shows more of the name."""
        if event.widget is not tree or event.width < 40:
            return
        target = max(140, event.width - 22)
        if abs(int(tree.column("name", "width")) - target) < 4:
            return
        tree.column("name", width=target)

    def _fit_course(self, tree, event):
        """Keep the course text inside its pane. A wider column paints over the next list."""
        if event.widget is not tree or event.width < 40:
            return
        fixed = 0
        for key in ("progress", "score", "id", "track"):
            if key in tree["columns"]:
                fixed += int(tree.column(key, "width"))
        target = max(80, event.width - fixed - 22)
        if abs(int(tree.column("course", "width")) - target) < 4:
            return
        tree.column("course", width=target)

    def _layout(self):
        """Show the next list when one is chosen. Dividers stay draggable."""
        show_mod = self.subject_i is not None
        show_course = show_mod and self.module_i is not None
        shown = (show_mod, show_course)
        if shown == self._shown:
            return
        for pane in list(self.panes.panes()):
            self.panes.forget(pane)
        self.panes.add(self.sub_frame, weight=1)
        if show_mod:
            self.panes.add(self.mod_frame, weight=2)
        if show_course:
            self.panes.add(self.course_frame, weight=3)
        self._shown = shown
        self.root.after_idle(self._place_sashes)

    def _apply_geometry(self):
        sw = max(self.root.winfo_screenwidth(), 1)
        sh = max(self.root.winfo_screenheight(), 1)
        try:
            box = (
                self.root.winfo_vrootx(),
                self.root.winfo_vrooty(),
                self.root.winfo_vrootwidth(),
                self.root.winfo_vrootheight(),
            )
        except tk.TclError:
            box = (0, 0, sw, sh)
        if box[2] < 200 or box[3] < 200:
            box = (0, 0, sw, sh)
        fitted = fit_geometry(self._normal_geometry or "", *box)
        chosen = fitted or screen_geometry(sw, sh)
        self._normal_geometry = chosen
        self.root.geometry(chosen)

    def _finish_open(self):
        """Maximize after the first size is applied, then start remembering drags."""
        self._restoring = True
        if self._saved_zoom:
            self._zoom()
        self.root.after(250, self._mark_ready)

    def _mark_ready(self):
        self._restoring = False
        self._ui_ready = True

    def _zoom(self):
        try:
            if self.root.tk.call("tk", "windowingsystem") == "win32":
                self.root.state("zoomed")
                return
        except tk.TclError:
            pass
        try:
            self.root.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass
        try:
            self.root.state("zoomed")
        except tk.TclError:
            return

    def _is_zoomed(self) -> bool:
        try:
            if self.root.tk.call("tk", "windowingsystem") == "win32":
                return str(self.root.state()) == "zoomed"
        except tk.TclError:
            return False
        try:
            return bool(self.root.attributes("-zoomed"))
        except tk.TclError:
            return False

    def _on_configure(self, event):
        if event.widget is not self.root or not self._ui_ready or self._restoring:
            return
        if self._save_after is not None:
            try:
                self.root.after_cancel(self._save_after)
            except tk.TclError:
                pass
        self._save_after = self.root.after(400, self._save_window)

    def _on_sash(self, _event):
        self._remember_sashes()
        if self._ui_ready:
            self._save_window()

    def _remember_sashes(self):
        try:
            count = len(self.panes.panes())
            if count < 2:
                return
            positions = [int(self.panes.sashpos(i)) for i in range(count - 1)]
        except tk.TclError:
            return
        if any(pos < 40 for pos in positions):
            return
        self._sash_memory[str(count)] = positions

    def _save_window(self):
        self._save_after = None
        if not self._ui_ready:
            return
        try:
            zoomed = self._is_zoomed()
            if not zoomed:
                self._normal_geometry = self.root.geometry()
            self._remember_sashes()
            remember_window(self._normal_geometry, zoomed, self._sash_memory)
        except tk.TclError:
            return

    def _place_sashes(self):
        try:
            self.panes.update_idletasks()
            width = self.panes.winfo_width()
        except tk.TclError:
            return
        if width < 200:
            return
        n = len(self.panes.panes())
        saved = self._sash_memory.get(str(n))
        try:
            if n >= 2 and isinstance(saved, list) and len(saved) == n - 1:
                for i in range(n - 2, -1, -1):
                    room = width - 80 - (n - 2 - i) * 80
                    self.panes.sashpos(i, max(80, min(int(saved[i]), room)))
                return
            if n == 2:
                self.panes.sashpos(0, max(280, min(int(width * 0.42), width - 160)))
            elif n >= 3:
                self.panes.sashpos(1, max(280, min(int(width * 0.62), width - 160)))
                self.panes.sashpos(0, max(200, min(int(width * 0.30), width - 320)))
        except tk.TclError:
            return

    def _pick_root(self):
        p = filedialog.askdirectory(title=t(self.locale, "courses_folder"))
        if p:
            self.courses_root = Path(p)
            if portable():
                remember_courses(self.courses_root)
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
        for i, sub in enumerate(self.catalog.get("subjects") or []):
            tree.insert("", "end", iid=str(i), values=(sub.get("name") or "",))
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
        for i, mod in enumerate(modules):
            tree.insert("", "end", iid=str(i), values=(mod.get("name") or "",))
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
        self._ui_ready = True
        self._save_window()
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
        cmd = _foolbook_cmd(path, cid, str(self.progress.path))
        if cmd is None:
            messagebox.showwarning(t(self.locale, "app"), t(self.locale, "no_foolbook"))
            return
        if self._viewer and self._viewer.poll() is None:
            self._viewer.terminate()
            try:
                self._viewer.wait(timeout=2)
            except Exception:
                self._viewer.kill()
        previous = getattr(self, "_viewer_log", None)
        if previous is not None:
            try:
                previous.close()
            except OSError:
                pass
        log_path = self.progress.path.with_name("foolbook.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = open(log_path, "w", encoding="utf-8")
        self._viewer = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        self._viewer_log = log
        self.progress.touch(cid)
        self._fill_courses()
        self.status.config(text=f"Opened {cid}")
        self.root.after(800, self._check_viewer)

    def _check_viewer(self):
        viewer = self._viewer
        if viewer is None or viewer.poll() is None:
            return
        log = getattr(self, "_viewer_log", None)
        if log is not None:
            try:
                log.close()
            except OSError:
                pass
        text = ""
        path = self.progress.path.with_name("foolbook.log")
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()[-800:]
        except OSError:
            pass
        messagebox.showerror(
            t(self.locale, "app"),
            text or f"Foolbook exited ({viewer.returncode}).",
        )



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

