"""Progression and scores.

The viewer records visited pages, the last page, and quiz answers.
Foolcourse reads the same file to show progress and scores.

Stored as progress/progress.json, which is gitignored.

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


def default_path() -> Path:
    """Shared progress file used by the viewer and Foolcourse."""
    root = Path(__file__).resolve().parents[1]
    dest = root / "progress" / "progress.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


class Progress:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else default_path()
        self.data: dict = {"courses": {}}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {"courses": {}}
        self.data.setdefault("courses", {})

    def reload(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return
        self.data.setdefault("courses", {})

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
        rec = self._ensure(course_id)
        rec["opened"] = True
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
        rec = self._ensure(course_id)
        rec["completed"] = True
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

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
