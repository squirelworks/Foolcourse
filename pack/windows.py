"""Build a Windows folder that runs without installing Python.

    python3 pack/windows.py

The folder is dist/Foolcourse-windows/. Double-click Foolcourse.bat.
The NIDA curriculum is inside it. The first start asks where the courses are.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "pack" / "cache"
DIST = ROOT / "dist" / "Foolcourse-windows"
ZIP = ROOT / "dist" / "Foolcourse-windows.zip"
FOOLBOOK = Path("/tmp/Foolbook")
OPENSCRIPT = Path("/tmp/repos/openscript_analysis")
CPYTHON = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/"
    "20261021/cpython-3.12.15+20261021-x86_64-pc-windows-msvc-install_only.tar.gz"
)

SKIP = {".git", "__pycache__", ".venv", "dist", "documentation", "pack", "openscript_analysis"}


def download(url: str, dest: Path) -> Path:
    if dest.is_file() and dest.stat().st_size > 0:
        print(f"cached {dest.name}", flush=True)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"get {url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "foolcourse-pack"})
    with urllib.request.urlopen(req, timeout=180) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(dest)
    return dest


def ignore(_dir: str, names: list[str]) -> set[str]:
    return {name for name in names if name in SKIP or name.endswith(".pyc")}


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=ignore)


def unpack_wheel(path: Path, dest: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if ".dist-info/" in info.filename:
                continue
            archive.extract(info, dest)


def write_text(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))


def main() -> int:
    if not FOOLBOOK.is_dir() or not OPENSCRIPT.is_dir():
        raise SystemExit("Foolbook and openscript_analysis checkouts are required")
    archive = download(CPYTHON, CACHE / "cpython-win.tar.gz")
    wheels = CACHE / "wheels"
    if not any(wheels.glob("*.whl")):
        wheels.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(
            [
                sys.executable, "-m", "pip", "download",
                "cryptography", "pillow", "cffi", "pycparser",
                "--dest", str(wheels),
                "--python-version", "312",
                "--platform", "win_amd64",
                "--only-binary=:all:",
            ]
        )

    if DIST.exists():
        shutil.rmtree(DIST)
    staging = CACHE / "cpython-win"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    print("extracting python", flush=True)
    subprocess.check_call(["tar", "-C", str(staging), "-xf", str(archive)])
    src = staging / "python"
    if not (src / "python.exe").is_file():
        raise SystemExit("archive has no python/python.exe")
    if not (src / "DLLs" / "_tkinter.pyd").is_file():
        raise SystemExit("this Python has no Tk")
    DIST.mkdir(parents=True)
    print("copying python", flush=True)
    shutil.copytree(src, DIST / "python")

    app = DIST / "app"
    app.mkdir()
    for wheel in sorted(wheels.glob("*.whl")):
        print(f"wheel {wheel.name}", flush=True)
        unpack_wheel(wheel, app)
    copy_tree(ROOT / "foolcourse", app / "foolcourse")
    for name in ("foolbook", "engine", "viewer", "progress", "menu", "modules"):
        found = FOOLBOOK / name
        if found.is_dir():
            copy_tree(found, app / name)
    copy_tree(OPENSCRIPT, app / "openscript_analysis")
    curriculum = DIST / "_curriculum"
    curriculum.mkdir()
    for name in ("nida.curriculum.json", "nida.programs.xml"):
        shutil.copy2(ROOT / "_curriculum" / name, curriculum / name)

    write_text(DIST / "Foolcourse.bat", """@echo off
cd /d "%~dp0"
set "FOOLCOURSE_HOME=%~dp0"
set "PYTHONPATH=%~dp0app"
start "" "%~dp0python\\pythonw.exe" -m foolcourse
""")
    write_text(DIST / "Foolcourse-console.bat", """@echo off
cd /d "%~dp0"
set "FOOLCOURSE_HOME=%~dp0"
set "PYTHONPATH=%~dp0app"
"%~dp0python\\python.exe" -m foolcourse
if errorlevel 1 pause
""")
    write_text(DIST / "START.txt", """Foolcourse for Windows

1. Unzip this whole folder. Do not run it from inside the zip.
2. Double-click Foolcourse.bat.
3. When it asks where the courses are, pick the folder that holds the .tbk files.
4. It remembers that folder. The curriculum is already in _curriculum and is not something you pick.

Foolcourse-console.bat does the same thing with a window that stays open if it fails.
""")

    if ZIP.exists():
        ZIP.unlink()
    print("zipping", flush=True)
    shutil.make_archive(str(ZIP.with_suffix("")), "zip", DIST.parent, DIST.name)
    print(f"wrote {ZIP} ({ZIP.stat().st_size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
