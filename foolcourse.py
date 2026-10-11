#!/usr/bin/env python3
"""Foolcourse launcher.

Catalogs a courses folder and opens the selected course in Foolbook.
Scores are kept per course. The overall score counts only courses that
are part of 03_ATT_Master.

  python3 foolcourse.py                         # catalog _courses/
  python3 foolcourse.py path/to/courses         # catalog that folder
  python3 foolcourse.py path/to/courses --xml courses.xml
  python3 foolcourse.py --list path/to/courses  # print, no window
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from foolcourse.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
