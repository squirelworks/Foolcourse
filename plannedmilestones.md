# Foolcourse milestones

Foolcourse is a course platform. ATT is one use of it, not the product.

A deployment has an official course list. Anything not on that list is
extra material. Extra material is catalogued, can be opened, and keeps
its own score. It does not count toward the overall score.

## v1.0.0

Catalog a courses folder and open the selected book in Foolbook.

Done:

- Lists courses by subject and module
- Opens the selected book in Foolbook
- Saves progress and a score per course
- Overall score counts only the official list

ATT is the first official list: `03_ATT_Master`, or the `0_MASTER3` /
ATT Master_3 menu in a `courses.xml`. Rating-track-only lessons and
anything else on disk are extra.

## v1.x

Make the official list a property of the deployment, not of ATT.

- Curriculum maker: name a curriculum, mark the official list, save a
  curriculum file. Anything not marked is extra material.

- An official list is named by the deployment: a folder, a menu in a
  catalog file, or an explicit id set. ATT Master is one such list.
- Extra material is everything not on that list. It stays in the
  catalog, keeps its own score, and is left out of the overall.
- A second deployment can point at its own courses folder and its own
  official list without any ATT names in the path.
- The window labels the official track by the list's name, not by
  "ATT Master", unless that is the list in use.

## v2.0.0 (planned)

A functional platform for more than one curriculum.

- More than one official list in one catalog, each with its own overall
- Extra material can be grouped (supplements, drills, outside reading)
  without becoming official
- Progress and scores travel with the learner, not with one curriculum
