#!/usr/bin/env python3
"""Foolcourse launcher.

Catalogs a courses folder and opens the selected course in Foolbook.
Scores are kept per course. The overall counts only the official list.
The package lives in main/.

  python3 foolcourse.py                         # catalog _courses/
  python3 foolcourse.py path/to/courses         # catalog that folder
  python3 foolcourse.py path/to/courses --xml courses.xml
  python3 foolcourse.py --theme modern          # not the Win95 look
python3 foolcourse.py --list path/to/courses  # print, no window
  python3 foolcourse.py --make path/to/courses  # curriculum maker
  python3 foolcourse.py --student alex        # _student/alex.json
python3 foolcourse.py --port 8080             # viewer port, default 1337
python3 foolcourse.py path/to/courses --curriculum file.json
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from main.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
