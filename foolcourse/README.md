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

A courses folder can be flat or nested. A course under a folder named
`03_ATT_Master` (also `ATT_Master`, `0_MASTER3`) is official.

```
courses/
  03_ATT_Master/
    DC Circuits/
      93951100.tbk
  Other/
    something.tbk
```

With `--xml courses.xml` the hierarchy and titles come from the Navy
ATT menu export. Lessons in the `0_MASTER3` / ATT Master_3 menu are
official. Lessons that only appear in a rating track are not.

## Scores

Foolbook writes page visits and quiz answers to `progress/progress.json`.
Each course keeps its own score (best percentage of quiz answers).
The overall score is the mean of those best percentages for official
courses only. A course outside `03_ATT_Master` still has a score; it is
not added into the overall.
