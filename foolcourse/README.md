# Foolcourse

Catalogs a courses folder and opens the selected course in Foolbook.

```bash
python3 foolcourse.py                         # catalog _courses/
python3 foolcourse.py path/to/courses         # catalog that folder
python3 foolcourse.py path/to/courses --xml courses.xml
python3 foolcourse.py --list path/to/courses  # print, no window
python3 -m foolbook --course path/to/courses
```

## Layout

A courses folder can be flat or nested. The folder names are the subject
and the module when you do not pass a menu. A curriculum file, not a
folder name, decides which courses count.

```
courses/
  Getting around/
    Street sense/
      phone.fbk
```

With `--xml menu.xml` the subjects, modules, and titles come from that
menu.

## Scores

Foolbook writes page visits and quiz answers to `progress/progress.json`.
Each course keeps its own score (best percentage of quiz answers).
The overall score is the mean of those best percentages for official
courses only. A course that is not on the official list still has a score;
it is not added into the overall.
