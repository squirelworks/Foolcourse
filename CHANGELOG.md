# Changelog
## 1.0.0r6

- A Windows folder you unzip and double-click. It loads the NIDA curriculum that sits beside it, then asks where the courses are, and remembers that folder.
- Depends on Foolbook 1.0.5r32.

## 1.0.0r5

- Depends on Foolbook 1.0.5r32, not 1.0.2.

## 1.0.0r4

- NIDA program list: `_curriculum/nida.curriculum.json` and `_curriculum/nida.programs.xml`.
- A three-level menu keeps the unit. "DC Circuits / Introduction to Electricity" is not folded into "DC Circuits".

## 1.0.0r3

- Depends on Foolbook 1.0.2.


## 1.0.0r1

- Package is now `foolcourse`. No more `main` collision.


## 1.0.0

Catalogs a courses folder and opens the selected book in Foolbook.

- Lists courses by subject and module
- Official list and extras. Overall score counts only the official list
- Opens the selected book in Foolbook on port 1337
- One viewer. The next Open replaces it instead of starting another
- Progress and a score per course, stored in an encrypted `.fcs`
- `--locale`, including `klingon`. Passed to Foolbook
- `--theme modern`
- Example modules: Street sense, Filing taxes
- Filing taxes ships best-effort `.tbk` shells. Not books the 8.1 engine would open

Depends on Foolbook 1.0.1.

## 0.9.0

First release.

## 1.0.0r2

- Launches native Foolbook with book path; no server
- Ships example courses
- --freshstart and --doctor
- _debug/ dumps diagnostics

