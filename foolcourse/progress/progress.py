"""Progression and scores.

The viewer records visited pages, the last page, and quiz answers.
Foolcourse reads the same file to show progress and scores.

Stored as an encrypted .fcs under _student/. Default is
_student/student.fcs. Extracted, it is JSON. On disk it needs the
password. A later module can replace that password.

Score model
-----------
Each course keeps the quiz answers it has seen. A course score is the
percentage of those answers that were correct, and the best percentage
is kept. The overall score is the mean of the best percentages for
courses that belong to the official track (03_ATT_Master / ATT Master).
Courses outside that track still have their own score; they are not
added into the overall.
"""

from __future__ import annotations

import json
from pathlib import Path

from foolcourse.progress.fcs import pack, unpack


def student_dir() -> Path:
    """Folder that holds student files."""
    root = Path(__file__).resolve().parents[1]
    dest = root / "_student"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def student_path(name: str = "student") -> Path:
    """Path for a student. A bare name is _student/<name>.fcs."""
    raw = (name or "student").strip()
    path = Path(raw)
    if path.suffix.lower() in (".json", ".fcs") or "/" in raw or raw.startswith("."):
        path = path.expanduser()
        if not path.is_absolute():
            path = student_dir().parent / path
        return path
    return student_dir() / f"{raw}.fcs"


def default_path() -> Path:
    """The student file Foolcourse and the viewer share."""
    return student_path("student")


class Progress:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_path()
        self.data: dict = self._blank()
        if self.path.exists():
            try:
                self.data = self._read()
            except Exception:
                self.data = self._blank()
        self._normalize()

    def reload(self) -> None:
        if self.path.exists():
            try:
                self.data = self._read()
            except Exception:
                return
        self._normalize()

    def label(self, course_id: str) -> str:
        """Short progress text for the catalog."""
        rec = self._rec(course_id)
        if rec.get("completed"):
            return "done"
        n = len(rec.get("visited") or [])
        if n:
            return f"{n} pages"
        if rec.get("opened"):
            return "opened"
        return ""

    def status(self, course_id: str) -> str:
        rec = self._rec(course_id)
        if rec.get("completed"):
            return "done"
        if rec.get("opened"):
            return "started"
        return ""

    def touch(self, course_id: str) -> None:
        if not course_id:
            return
        from datetime import date
        rec = self._ensure(course_id)
        rec["opened"] = True
        today = date.today().isoformat()
        if not self.data.get("started"):
            self.data["started"] = today
        self.data["last_seen"] = today
        self._save()

    def mark_page(self, course_id: str, page_id: str) -> None:
        """Record that a page was visited."""
        if not course_id or not page_id:
            return
        rec = self._ensure(course_id)
        rec["opened"] = True
        visited = rec.setdefault("visited", [])
        if page_id not in visited:
            visited.append(page_id)
        rec["last_page"] = page_id
        self._save()

    def last_page(self, course_id: str) -> str:
        return self._rec(course_id).get("last_page") or ""

    def visited(self, course_id: str) -> list[str]:
        return list(self._rec(course_id).get("visited") or [])

    def complete(self, course_id: str) -> None:
        if not course_id:
            return
        from datetime import date
        rec = self._ensure(course_id)
        rec["completed"] = True
        rec.setdefault("completed_on", date.today().isoformat())
        self._save()

    def record_answer(self, course_id: str, page_id: str, correct: bool) -> None:
        """Record one quiz answer. Keeps the best percentage for the course."""
        if not course_id or not page_id:
            return
        rec = self._ensure(course_id)
        rec["opened"] = True
        score = rec.setdefault("score", {})
        answers = score.setdefault("answers", {})
        # One result per quiz page. A later try replaces the earlier one
        # so a retry does not inflate the total.
        answers[page_id] = bool(correct)
        correct_n = sum(1 for v in answers.values() if v)
        answered = len(answers)
        percent = (100.0 * correct_n / answered) if answered else 0.0
        score["correct"] = correct_n
        score["answered"] = answered
        score["percent"] = round(percent, 1)
        best = score.get("best")
        score["best"] = round(percent, 1) if best is None else round(max(best, percent), 1)
        rec["attempts"] = int(rec.get("attempts") or 0) + 1
        self._save()

    def set_score(self, course_id: str, percent: float, max_score: float = 100.0) -> None:
        """Set a course score directly. Used when the score is not from a quiz."""
        if not course_id:
            return
        rec = self._ensure(course_id)
        score = rec.setdefault("score", {})
        pct = max(0.0, min(100.0, float(percent)))
        score["percent"] = round(pct, 1)
        score["best"] = round(pct, 1)
        score["max"] = max_score
        self._save()

    def course_score(self, course_id: str) -> dict:
        score = self._rec(course_id).get("score") or {}
        return {
            "correct": score.get("correct") or 0,
            "answered": score.get("answered") or 0,
            "percent": score.get("percent"),
            "best": score.get("best"),
        }

    def overall(self, official_ids: list[str] | set[str]) -> dict:
        """Mean of the best score for official courses that have one.

        Courses not in official_ids are ignored, even if they have a score.
        """
        official = {i for i in official_ids if i}
        scored = []
        excluded = 0
        for cid, rec in (self.data.get("courses") or {}).items():
            best = (rec.get("score") or {}).get("best")
            if best is None:
                continue
            if cid in official:
                scored.append(best)
            else:
                excluded += 1
        percent = round(sum(scored) / len(scored), 1) if scored else None
        return {
            "percent": percent,
            "scored": len(scored),
            "official": len(official),
            "excluded": excluded,
        }

    def _rec(self, course_id: str) -> dict:
        return (self.data.get("courses") or {}).get(course_id) or {}

    def _ensure(self, course_id: str) -> dict:
        return self.data.setdefault("courses", {}).setdefault(course_id, {})

    def student_name(self) -> str:
        return str(
            self.data.get("preferred_name")
            or self.data.get("name")
            or self.data.get("id")
            or self.path.stem
        )

    def set_locale(self, locale: str) -> None:
        if locale:
            self.data["locale"] = locale
            self._save()

    def _blank(self) -> dict:
        stem = self.path.stem or "student"
        return {
            "id": stem,
            "name": stem.replace("_", " ").title(),
            "preferred_name": "",
            "school_id": "",
            "cohort": "",
            "curriculum": "",
            "locale": "en",
            "theme": "",
            "port": None,
            "enrolled": "",
            "started": "",
            "last_seen": "",
            "courses": {},
        }

    def _normalize(self) -> None:
        if not isinstance(self.data, dict):
            self.data = self._blank()
        blank = self._blank()
        for key, value in blank.items():
            self.data.setdefault(key, value)
        self.data.setdefault("courses", {})

    def _read(self) -> dict:
        blob = self.path.read_bytes()
        if self.path.suffix.lower() == ".fcs" or blob[:4] == b"FCS1":
            return unpack(blob)
        return json.loads(blob.decode("utf-8"))

    def _save(self) -> None:
        self._normalize()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.suffix.lower() == ".fcs":
            self.path.write_bytes(pack(self.data))
        else:
            self.path.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
