# A deployment

## Official and extra

The official list is a curriculum file. A folder name does not decide
it, and a menu does not decide it. The menu supplies the subjects,
modules, and titles. The window labels the track by the list's name.

## Scores

Each course keeps its own score: quiz answers, a percent, and the best
percent seen. The overall is the mean of the best percentages for
courses on the official list.

A course that is not on the list still has a score. It is shown. It is
not added into the overall.

## A Windows, Linux, or Mac folder

The [1.0.1 release](https://github.com/squirelworks/Foolcourse/releases/tag/v1.0.1) has a zip for Windows, Linux x64, Linux ARM, and both Macs. Python is in that folder. The curriculum files in `_curriculum/` are the examples, not a deployment's courses.

`python3 pack/build.py all` builds the same folders into `dist/`.

Books go in `courses/`. They can sit in that folder or in a folder inside it. A book the course opens goes in there too. `python3 pack/build.py --zip windows-x64` writes the zip again after the books are in place. The same `--zip` name works for the other systems.

Unzip the whole folder. Windows double-clicks `Foolcourse.bat`. Linux runs `./Foolcourse.sh`. Mac double-clicks `Foolcourse.command`. If `courses/` already has books, the program uses it and does not ask. An empty folder asks once. Refresh picks up a book added later.

There is no Android or iOS copy. The window is Tk.

## A second deployment

Point Foolcourse at a different courses folder and a different
curriculum file. The same program, the same rules.

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
