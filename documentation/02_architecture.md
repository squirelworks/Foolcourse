# Architecture

Three repositories. They do not import each other. They meet at files.

```
Foolversity          writes the files
    |  .fcs  .curriculum.json  .school.json
    v
Foolcourse           catalogs, scores, launches
    |  a book path, --student, --locale, --course, --port
    v
Foolbook             opens the book and runs it
```

| program | release | job |
| --- | --- | --- |
| Foolversity | v0.9.0 | Make a student, a school, a curriculum |
| Foolcourse | v0.9.0 | Catalog a folder, open a course, keep scores |
| Foolbook | v1.0.5r32 | Open a book, follow handlers, record progress |

## The boundary

From Foolversity `STANDARD.md`:

| file | who writes | who reads |
| --- | --- | --- |
| `.fcs` | Foolversity | Foolcourse and Foolbook, each with its own opener |
| `.curriculum.json` | Foolversity | Foolcourse |
| `.school.json` | Foolversity | Foolversity |

`.school.json` is Foolversity's own file. Foolcourse does not read it.

Each side owns its copy of the opener. A change to the envelope is a
change to the standard, agreed in writing, not a shared import.

## How a course opens

1. Foolcourse scans `_courses/` (or the folder it was given).
2. A curriculum file marks which course ids are official.
3. The window lists subjects, modules, and courses. Official and extra
   are both shown. The overall counts only the official list.
4. Open launches Foolbook with the book path and `--course`. Foolcourse
   does not serve the book.
5. Finish in the viewer writes the score back to the `.fcs`.

One viewer. The next Open stops the viewer Foolcourse started and
starts the next course.


## Place in the stack

Foolversity holds the courses.
Foollege holds the students.
Foolcourse holds the instruction.
Foolbook opens the book.

A curriculum is figured out on its own. OpenScript lets an old ToolBook be reused.
