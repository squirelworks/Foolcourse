# A deployment

## Official and extra

The official list is a property of the deployment, not of ATT.

It can be named three ways:

- a curriculum file, which is the normal way
- a folder whose name is `03_ATT_Master`, `ATT_Master`, or `0_MASTER3`
- a menu in a `courses.xml`, where the `0_MASTER3` / ATT Master_3 menu
  is the official list and rating-track-only lessons are extra

The window labels the official track by the list's name. It says
"ATT Master" only when that is the list in use.

## Scores

Each course keeps its own score: quiz answers, a percent, and the best
percent seen. The overall is the mean of the best percentages for
courses on the official list.

A course that is not on the list still has a score. It is shown. It is
not added into the overall.

## A second deployment

Point Foolcourse at a different courses folder and a different
curriculum file. No ATT names are required in the path. The same
program, the same rules.

Foolversity makes the curriculum file and the student file for that
deployment. `--out` writes them into the Foolcourse tree.

## What is shipped as an example

`_courses/` holds two example modules.

- Getting around / Street sense. `phone` is the example official course:
  how to not walk while using your phone. It has a Klingon overlay.
- Money / Filing taxes. Nine short courses on a US tax year, plus three
  that teach the figures change and where the official numbers live.
  These are a map, not a preparer. Confirm on IRS.gov.

`_curriculum/example.curriculum.json` is the default.
`_curriculum/taxes.curriculum.json` is the tax module.
