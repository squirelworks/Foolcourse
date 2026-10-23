# Current state

Foolcourse 1.0.0r5. Foolversity v0.9.0. Foolbook v1.0.5r32.

## Foolcourse does

- Catalogs `_courses/` or a folder it is given
- Lists by subject and module
- Loads a curriculum file and treats its list as official
- Opens the selected book by launching Foolbook with the book path.
  No server of its own
- Keeps one viewer. The next Open stops it and starts the next course
- Saves progress and a score per course in an encrypted `.fcs`
- Computes an overall from the official list only
- `--locale`, passed through to Foolbook. `klingon` is accepted
- `--theme modern`
- `--student` names the `.fcs`
- `--make` opens the curriculum maker
- `--doctor` writes diagnostics
- `--freshstart` clears progress for a clean run
- `_debug/` holds diagnostic dumps
- Package is `foolcourse`. The old `main` name is gone

## Foolversity does

- `student`, `school`, `curriculum` from the command line
- `gui` opens the same three as forms
- `--out` targets a Foolcourse tree

## Foolbook does

- Opens `.fbk` and `.tbk`
- Follows next, back, and goto
- Serves its own viewer when run on its own
- Finish records the quiz, marks the course complete, saves the score
- Applies a course locale overlay when the course has one
- Compiles OpenScript and can export a `.tbk` shell

## Known rough edges

- The `.fcs` password is a placeholder.
- Locale overlay files must not be listed as courses. The catalog skips
  `*.klingon.json`. A new locale must be skipped the same way.
- A viewer Foolcourse did not start is left alone.
