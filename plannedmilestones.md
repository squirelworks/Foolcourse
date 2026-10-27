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

The official list is a curriculum file. A folder name does not mark a
course official, and a menu does not either. The menu is subjects,
modules, and titles. Anything not on the curriculum is extra.

## v1.x

Make the official list a property of the deployment.

- Curriculum maker: name a curriculum, mark the official list, save a
  curriculum file. Anything not marked is extra material.

- An official list is an explicit id set in that file.
- Extra material is everything not on that list. It stays in the
  catalog, keeps its own score, and is left out of the overall.
- A second deployment can point at its own courses folder and its own
  official list.
- The window labels the official track by the list's name.

## v2.0.0 (planned)

A functional platform for more than one curriculum.

- More than one official list in one catalog, each with its own overall
- Extra material can be grouped (supplements, drills, outside reading)
  without becoming official
- Progress and scores travel with the learner, not with one curriculum
- A system's procedures stay in its `.fsk`. Foolbook runs that file.
  It does not keep its own copy of `initializeBase`, `setupMenuPage`,
  or the rest. Foolcourse 1 may still call a Python stand-in. Foolcourse 2
  does not add another one.
