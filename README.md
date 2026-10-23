# Foolcourse

Version 1.0.0. Depends on Foolbook 1.0.1.

A course platform. It catalogs a courses folder and opens the selected
course in Foolbook.

A deployment has an official course list. Anything not on that list is
extra material: it is catalogued, it can be opened, and it keeps its own
score, but it does not count toward the overall. ATT is one use of this.
Its official list is ATT Master; rating tracks and anything else are extra.

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
python3 foolcourse.py path/to/courses --curriculum att.curriculum.json
python3 foolcourse.py path/to/courses --xml _curriculum/nida.programs.xml --curriculum _curriculum/nida.curriculum.json
```

## Default folders

`_courses/` holds the books. `_curriculum/` holds curriculum files and is the default. With no arguments, Foolcourse catalogs `_courses/` and loads `_curriculum/example.curriculum.json`.

The example official course is `phone`: how to not walk while using your phone. `reading_maps` and `bus_times` are extra and do not exist.

## Curriculum maker

`--make` opens a window over the courses folder. Mark courses official
or extra, name the curriculum and the official list, and save a
curriculum file. `--curriculum` loads that file: the overall counts only
its official list, and the window labels the track by that list's name.

ATT is one curriculum. A second deployment makes its own file.

## Layout

A course under a folder named `03_ATT_Master` (also `ATT_Master`, `0_MASTER3`) is official.

```
courses/
  03_ATT_Master/
    DC Circuits/
      93951100.tbk
  Other/
    something.tbk
```

With `--xml courses.xml` the hierarchy and titles come from the Navy ATT menu export. Lessons in the `0_MASTER3` / ATT Master_3 menu are official. Lessons that only appear in a rating track are not.

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
