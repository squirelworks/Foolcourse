"""Build the Windows folder. Same as pack/build.py windows-x64.

    python3 pack/windows.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build import main


if __name__ == "__main__":
    raise SystemExit(main(["windows-x64", *sys.argv[1:]]))
