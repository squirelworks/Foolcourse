# Foolcourse

Version 1.0.1r2. The Windows folder uses Foolbook at 1339017. The 1.0.1 Linux and macOS folders are unchanged.

From scratch, paste this. It clones the repo if it is missing, stays on `main`, and opens the catalog.

```bash
mkdir -p ~/FU
cd ~/FU
if [ ! -d Foolcourse/.git ]; then
  git clone https://github.com/squirelworks/Foolcourse.git
fi
cd Foolcourse
git fetch origin
git checkout -B main origin/main
git pull --ff-only origin main
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e .
python3 -m foolcourse
```

## A copy for someone else

The downloads are on the [1.0.1 release](https://github.com/squirelworks/Foolcourse/releases/tag/v1.0.1). The current Windows folder is [1.0.1r2](https://github.com/squirelworks/Foolcourse/releases/tag/v1.0.1r2): `Foolcourse-1.0.1r2-windows-x64.zip`. Python is inside the folder. Nobody installs it.

| file | how it starts |
| --- | --- |
| `Foolcourse-1.0.1-windows-x64.zip` | Unzip the whole folder. Double-click `Foolcourse.bat`. |
| `Foolcourse-1.0.1-linux-x64.zip` | Unzip. In a terminal: `./Foolcourse.sh` |
| `Foolcourse-1.0.1-linux-arm64.zip` | Same, for a 64-bit ARM machine. |
| `Foolcourse-1.0.1-macos-arm64.zip` | Unzip. Double-click `Foolcourse.command`. Apple silicon. |
| `Foolcourse-1.0.1-macos-x64.zip` | Same, for an Intel Mac. |

Put the books in the `courses` folder before you zip it for someone, or they can put the books there after they unzip. A book can sit in that folder or in a folder inside it. If a course opens another book, that file goes in `courses` too. If `courses` already has books, Foolcourse does not ask where they are. `START.txt` in the folder is the note they read.

There is no Android build and no iOS build. The window is Tk. A phone does not run it.

To build the folders yourself:

```bash
python3 pack/build.py all
```

One system is `python3 pack/build.py windows-x64`. After you drop books into `dist/Foolcourse-1.0.1-windows-x64/courses`, zip again with `python3 pack/build.py --zip windows-x64`.

## What it is

A course platform. It catalogs a courses folder and opens the selected
course in Foolbook.

A deployment has an official course list. Anything not on that list is
extra material: it is catalogued, it can be opened, and it keeps its own
score, but it does not count toward the overall. The list is a curriculum
file. Foolcourse does not ship one deployment's courses.

Foolcourse is not affiliated with Asymetrix, Click2learn, or SumTotal.

```bash
python3 foolcourse.py                         # catalog _courses/
python3 foolcourse.py path/to/courses         # catalog that folder
python3 foolcourse.py path/to/courses --xml courses.xml
python3 foolcourse.py --theme modern          # not the Win95 look
python3 foolcourse.py --list path/to/courses  # print, no window
python3 foolcourse.py --make path/to/courses  # curriculum maker
python3 foolcourse.py --student alex        # _student/alex.fcs
python3 foolcourse.py --port 8080             # viewer port, default 1337
python3 foolcourse.py path/to/courses --curriculum path/to/curriculum.json
python3 foolcourse.py path/to/courses --xml path/to/menu.xml --curriculum path/to/curriculum.json
```

## Default folders

`_courses/` holds the books in a source checkout. `_curriculum/` holds curriculum files and is the default. With no arguments, Foolcourse catalogs `_courses/` and loads `_curriculum/example.curriculum.json`.

The Windows folder is different. Books go in `courses/` next to `Foolcourse.bat`. Whatever curriculum files are in `_curriculum/` are packed with it. The example is the one it loads when you do not name another.

The example official course is `phone`: how to not walk while using your phone. `reading_maps` and `bus_times` are extra and do not exist.

## Curriculum maker

`--make` opens a window over the courses folder. Mark courses official
or extra, name the curriculum and the official list, and save a
curriculum file. `--curriculum` loads that file: the overall counts only
its official list, and the window labels the track by that list's name.

## Layout

A course can sit in `courses/` or in a folder inside it. The folder names
are the subject and the module when you do not pass a menu. They do not
decide which courses count.

```
courses/
  Getting around/
    Street sense/
      phone.fbk
  Money/
    Filing taxes/
      do_i_file.fbk
```

With `--xml menu.xml` the subjects, modules, and titles come from that
menu. Which of those courses count is still the curriculum file.

## Scores

Page visits and quiz answers are stored in `progress/progress.json`. Each course keeps its own score. The overall score is the mean of the best percentages for courses on the official list only. Extra material still has a score; it is not added into the overall.

## Foolbook

Selecting a course launches [Foolbook](https://github.com/squirelworks/Foolbook). Foolcourse looks for `foolbook.py` beside itself, in a sibling `Foolbook/` checkout, or at the path in `FOOLBOOK`.

## Other repositories

Foolcourse does not import Foolversity or Foolbook.
Foolversity writes `.fcs` and `.curriculum.json`. Foolcourse reads them.
Foolbook is launched as a program and handed the student file.
The contract is the files, not shared source.

## Documentation

`documentation/` is the project record: intent, architecture, formats, and where it is going. Start at `documentation/00_index.md`.
