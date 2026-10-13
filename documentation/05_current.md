# Current state

Foolcourse v0.9.0. Foolversity v0.9.0. Foolbook v1.0.0r1.
Released 12 October 2026.

## Foolcourse does

- Catalogs `_courses/` or a folder it is given
- Lists by subject and module
- Loads a curriculum file and treats its list as official
- Opens the selected book in Foolbook
- Keeps one viewer. The next Open replaces it
- Saves progress and a score per course in an encrypted `.fcs`
- Computes an overall from the official list only
- `--locale`, passed through to Foolbook. `klingon` is accepted
- `--theme modern` for a window that is not the Win95 look
- `--port`, default 1337
- `--student` names the `.fcs`
- `--make` opens the curriculum maker

## Foolversity does

- `student`, `school`, `curriculum` from the command line
- `gui` opens the same three as forms
- `--out` targets a Foolcourse tree

## Foolbook does

- Opens `.fbk` and `.tbk`
- Follows next, back, and goto
- Serves a browser viewer on port 1337
- Finish records the quiz, marks the course complete, saves the score
- Applies a course locale overlay when the course has one
- Compiles OpenScript and can export a `.tbk` shell
- Opens the viewer with xdg-open. Chrome is the fallback

## Known rough edges

- The `.fcs` password is a placeholder.
- Locale overlay files must not be listed as courses. The catalog skips
  `*.klingon.json`. A new locale must be skipped the same way.
- The browser open fails on some desktops when Chrome is called
  directly. xdg-open is the path that works.
- A port held by a process Foolcourse did not start is reported, not
  killed.
