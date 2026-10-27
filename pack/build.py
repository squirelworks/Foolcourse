"""Build a folder that runs without installing Python.

    python3 pack/build.py all
    python3 pack/build.py windows-x64 linux-x64 macos-arm64

Each folder is dist/Foolcourse-<version>-<system>/. Put books in its
courses directory, then zip again with --zip and the same name.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "pack" / "cache"
DIST_ROOT = ROOT / "dist"
RELEASE = "20261021"
CPYTHON = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/"
    f"{RELEASE}/cpython-3.12.15+{RELEASE}-{{triple}}-install_only.tar.gz"
)

SKIP = {".git", "__pycache__", ".venv", "dist", "documentation", "pack", "openscript_analysis"}

# Android and iOS are not here. This program draws with Tk, and these
# CPython builds do not exist for those phones.
SPECS = {
    "windows-x64": {
        "triple": "x86_64-pc-windows-msvc",
        "pip": ["win_amd64"],
        "kind": "windows",
        "packages": ["cryptography==50.0.2", "cffi==2.1.1", "pillow", "pycparser"],
    },
    "linux-x64": {
        "triple": "x86_64-unknown-linux-gnu",
        "pip": ["manylinux_2_28_x86_64", "manylinux2014_x86_64", "manylinux_2_17_x86_64"],
        "kind": "unix",
        "packages": ["cryptography==46.0.0", "cffi==1.17.1", "pillow", "pycparser"],
    },
    "linux-arm64": {
        "triple": "aarch64-unknown-linux-gnu",
        "pip": ["manylinux_2_28_aarch64", "manylinux2014_aarch64", "manylinux_2_17_aarch64"],
        "kind": "unix",
        "packages": ["cryptography==46.0.0", "cffi==1.17.1", "pillow", "pycparser"],
    },
    "macos-arm64": {
        "triple": "aarch64-apple-darwin",
        "pip": ["macosx_11_0_arm64"],
        "kind": "mac",
        "packages": ["cryptography==50.0.2", "cffi==2.1.1", "pillow", "pycparser"],
    },
    "macos-x64": {
        "triple": "x86_64-apple-darwin",
        "pip": ["macosx_11_0_x86_64", "macosx_10_13_x86_64", "macosx_10_12_x86_64", "macosx_10_9_x86_64"],
        "kind": "mac",
        # Intel Mac wheels of cryptography stopped at 42. cffi 2 has none.
        "packages": ["cryptography==42.0.8", "cffi==1.17.1", "pillow", "pycparser"],
    },
}


def version() -> str:
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("pyproject.toml has no version")


def _checkout(name: str) -> Path:
    found = [
        ROOT.parent / name,
        Path("/tmp/scope") / name,
        Path("/tmp") / name,
        Path("/tmp/repos") / name,
    ]
    for path in found:
        if path.is_dir() and (path / "pyproject.toml").is_file():
            return path
    raise SystemExit(f"{name} checkout not found")


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


def write_text(path: Path, text: str, *, crlf: bool = False, executable: bool = False) -> None:
    newline = "\r\n" if crlf else "\n"
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def wheels_for(spec: dict, dest: Path) -> None:
    names = [
        item.split("==", 1)[0].split("[", 1)[0].replace("_", "-").lower()
        for item in spec["packages"]
    ]
    found = []
    if dest.is_dir():
        found = [
            path.name.split("-", 1)[0].replace("_", "-").lower()
            for path in dest.glob("*.whl")
        ]
    if all(name in found for name in names):
        print(f"cached wheels {dest.name}", flush=True)
        return
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    command = [
        sys.executable, "-m", "pip", "download",
        *spec["packages"],
        "--dest", str(dest),
        "--python-version", "312",
        "--implementation", "cp",
        "--abi", "cp312",
        "--only-binary=:all:",
        # The folder is Python 3.12. A host on 3.14 would re-resolve
        # cryptography's marker and demand a cffi that 3.12 does not use.
        "--no-deps",
    ]
    for platform in spec["pip"]:
        command.extend(["--platform", platform])
    subprocess.check_call(command)


def has_tk(python_root: Path) -> bool:
    return any(python_root.rglob("_tkinter*"))


def zip_dir(folder: Path, archive: Path) -> None:
    if archive.exists():
        archive.unlink()
    print("zipping", flush=True)
    shutil.make_archive(str(archive.with_suffix("")), "zip", folder.parent, folder.name)
    print(f"wrote {archive} ({archive.stat().st_size} bytes)", flush=True)


def build_one(key: str) -> Path:
    spec = SPECS[key]
    ver = version()
    folder = DIST_ROOT / f"Foolcourse-{ver}-{key}"
    archive = DIST_ROOT / f"Foolcourse-{ver}-{key}.zip"
    foolbook = _checkout("Foolbook")
    openscript = _checkout("openscript_analysis")
    tar = download(CPYTHON.format(triple=spec["triple"]), CACHE / f"{spec['triple']}.tar.gz")
    wheel_dir = CACHE / "wheels" / key
    wheels_for(spec, wheel_dir)

    if folder.exists():
        shutil.rmtree(folder)
    staging = CACHE / spec["triple"]
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    print(f"extracting {key}", flush=True)
    subprocess.check_call(["tar", "-C", str(staging), "-xf", str(tar)])
    src = staging / "python"
    exe = "python.exe" if spec["kind"] == "windows" else "bin/python3"
    if not (src / exe).is_file():
        raise SystemExit(f"{key}: archive has no {exe}")
    if not has_tk(src):
        raise SystemExit(f"{key}: this Python has no Tk, so the window cannot open")
    folder.mkdir(parents=True)
    print(f"copying {key}", flush=True)
    shutil.copytree(src, folder / "python")

    app = folder / "app"
    app.mkdir()
    for wheel in sorted(wheel_dir.glob("*.whl")):
        print(f"wheel {wheel.name}", flush=True)
        unpack_wheel(wheel, app)
    copy_tree(ROOT / "foolcourse", app / "foolcourse")
    for name in ("foolbook", "engine", "viewer", "progress", "menu", "modules"):
        found = foolbook / name
        if found.is_dir():
            copy_tree(found, app / name)
    core = foolbook / "core"
    if core.is_dir():
        copy_tree(core, app / "core")
    copy_tree(openscript, app / "openscript_analysis")
    curriculum = folder / "_curriculum"
    curriculum.mkdir()
    source = ROOT / "_curriculum"
    for path in sorted(source.glob("*.curriculum.json")):
        shutil.copy2(path, curriculum / path.name)
    for path in sorted(source.glob("*.xml")):
        shutil.copy2(path, curriculum / path.name)

    courses = folder / "courses"
    courses.mkdir()
    crlf = spec["kind"] == "windows"
    write_text(courses / "PUT COURSES HERE.txt", """Put the course files in this folder.

A .tbk or .fbk can sit here, or in a folder inside this one.
If a course opens another book, put that file in here too.
""", crlf=crlf)
    _launchers(folder, spec)
    return zip_dir(folder, archive) or archive


def _launchers(folder: Path, spec: dict) -> None:
    kind = spec["kind"]
    if kind == "windows":
        write_text(folder / "Foolcourse.bat", """@echo off
cd /d "%~dp0"
set "FOOLCOURSE_HOME=%~dp0"
set "PYTHONPATH=%~dp0app"
start "" "%~dp0python\\pythonw.exe" -m foolcourse
""", crlf=True)
        write_text(folder / "Foolcourse-console.bat", """@echo off
cd /d "%~dp0"
set "FOOLCOURSE_HOME=%~dp0"
set "PYTHONPATH=%~dp0app"
"%~dp0python\\python.exe" -m foolcourse
if errorlevel 1 pause
""", crlf=True)
        write_text(folder / "START.txt", """Foolcourse

1. Unzip this whole folder. Do not run it from inside the zip.
2. The courses go in the courses folder. If they are already there, leave them.
3. Double-click Foolcourse.bat.
4. Click a course to open it.

It remembers the courses folder. To add a course later, put the file in courses and click Refresh.

If the window does not open, double-click Foolcourse-console.bat and leave that window up.
""", crlf=True)
        return
    script = """#!/bin/sh
cd "$(dirname "$0")" || exit 1
export FOOLCOURSE_HOME="$PWD"
export PYTHONPATH="$PWD/app"
exec "$PWD/python/bin/python3" -m foolcourse
"""
    write_text(folder / "Foolcourse.sh", script, executable=True)
    if kind == "mac":
        write_text(folder / "Foolcourse.command", script, executable=True)
        write_text(folder / "START.txt", """Foolcourse

1. Unzip this whole folder. Do not run it from inside the zip.
2. The courses go in the courses folder. If they are already there, leave them.
3. Double-click Foolcourse.command.
4. Click a course to open it.

If macOS says it cannot be opened, right-click Foolcourse.command, choose Open, then Open again. This copy is not signed with Apple.

It remembers the courses folder. To add a course later, put the file in courses and click Refresh.
""")
        return
    write_text(folder / "START.txt", """Foolcourse

1. Unzip this whole folder. Do not run it from inside the zip.
2. The courses go in the courses folder. If they are already there, leave them.
3. Open a terminal in this folder and run: ./Foolcourse.sh
4. Click a course to open it.

It remembers the courses folder. To add a course later, put the file in courses and click Refresh.
""")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    zipping = "--zip" in argv
    argv = [item for item in argv if item != "--zip"]
    if not argv or argv == ["all"]:
        keys = list(SPECS)
    else:
        unknown = [item for item in argv if item not in SPECS]
        if unknown:
            raise SystemExit(f"unknown: {', '.join(unknown)}. known: {', '.join(SPECS)}")
        keys = argv
    if zipping:
        ver = version()
        for key in keys:
            folder = DIST_ROOT / f"Foolcourse-{ver}-{key}"
            archive = DIST_ROOT / f"Foolcourse-{ver}-{key}.zip"
            if not folder.is_dir():
                raise SystemExit(f"no folder to zip: {folder}")
            zip_dir(folder, archive)
        return 0
    for key in keys:
        build_one(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
