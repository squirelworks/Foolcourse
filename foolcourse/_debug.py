"""Foolcourse diagnostics.

  python3 -m foolcourse --doctor
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def run() -> int:
    print("Foolcourse doctor")
    print(f"  python: {sys.version.split()[0]}")
    print(f"  executable: {sys.executable}")
    here = Path(__file__).resolve().parent
    print(f"  package: {here}")
    for name in ("foolcourse", "foolbook", "openscript_analysis"):
        try:
            mod = importlib.import_module(name)
            print(f"  {name}: ok  {getattr(mod, '__file__', '?')}")
        except Exception as e:
            print(f"  {name}: FAIL  {e}")
    courses = here / "_courses"
    print(f"  courses: {courses}  exists={courses.exists()}")
    return 0
