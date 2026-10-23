"""Foolcourse localization.

--locale picks a catalog. klingon is a first-class id here. tlh is the
same catalog. A locale this module does not know falls back to en.
Course text is not translated. If a course has no localization, it shows
as written.
"""

from __future__ import annotations

_ALIASES = {
    "en": "en",
    "en_us": "en",
    "en-us": "en",
    "klingon": "klingon",
    "tlh": "klingon",
    "tlhingan": "klingon",
}

_CATALOGS = {
    "en": {
        "app": "Foolcourse",
        "courses_folder": "Courses folder",
        "courses_xml": "courses.xml",
        "refresh": "Refresh",
        "subject": "Subject",
        "module": "Module",
        "course": "Course",
        "progress": "Progress",
        "score": "Score",
        "id": "Id",
        "track": "Track",
        "open": "Open in Foolbook",
        "select_subject": "Select a subject",
        "select_module": "{n} modules. Select a module.",
        "select_course": "{n} courses. Double-click one to open it.",
        "overall_empty": "Overall ({name}): —   ({n} official)",
        "overall": "Overall ({name}): {pct:.0f}%   ({scored} of {n} scored)",
        "overall_other": "   {n} other scored, not counted",
        "official": "official",
        "done": "done",
        "pages": "{n} pages",
        "started": "started",
        "select_first": "Select a course first.",
        "not_found": "Course file not found:\n{path}",
        "no_foolbook": "Foolbook was not found.\nPut Foolbook next to Foolcourse, or set FOOLBOOK.",
        "all": "All",
        "ask_courses": "Choose the folder that holds the courses.\n\nThe curriculum is already part of this program.",
        "ask_courses_title": "Where are the courses?",
    },
    "klingon": {
        "app": "Foolcourse",
        "courses_folder": "paqmey",
        "courses_xml": "courses.xml",
        "refresh": "chu'",
        "subject": "ghu'",
        "module": "'ay'",
        "course": "ghojmeH paq",
        "progress": "ghojtaH",
        "score": "Qap",
        "id": "ID",
        "track": "He",
        "open": "Foolbook yIpoSmoH",
        "select_subject": "ghu' yIwIv",
        "select_module": "{n} 'ay'mey. 'ay' yIwIv.",
        "select_course": "{n} paqmey. wa' yIpoSmoH.",
        "overall_empty": "Hoch ({name}): —   ({n} ra'ta')",
        "overall": "Hoch ({name}): {pct:.0f}%   ({scored} / {n} Qapta')",
        "overall_other": "   {n} latlh Qapta', wej",
        "official": "ra'ta'",
        "done": "rIntaH",
        "pages": "{n} paqmey",
        "started": "taghpu'",
        "select_first": "ghojmeH paq yIwIv.",
        "not_found": "paq tu'be'lu':\n{path}",
        "no_foolbook": "Foolbook tu'be'lu'.\nFoolbook yIlan, pagh FOOLBOOK yIcher.",
        "all": "Hoch",
        "ask_courses": "paqmey Datu'bogh yIwIv.\n\nghojmeH paq tu'lu'pu'.",
        "ask_courses_title": "paqmey nuqDaq?",
    },
}


def resolve(locale: str | None) -> str:
    """Map a requested id to a catalog we have. Unknown ids stay as given."""
    key = (locale or "en").strip().lower().replace(" ", "_")
    return _ALIASES.get(key, key)


def known(locale: str | None) -> bool:
    return resolve(locale) in _CATALOGS


def t(locale: str | None, key: str, **fmt) -> str:
    """Look up a Foolcourse string. Missing keys and locales fall back to en."""
    cat = _CATALOGS.get(resolve(locale)) or _CATALOGS["en"]
    text = cat.get(key) or _CATALOGS["en"].get(key) or key
    return text.format(**fmt) if fmt else text
