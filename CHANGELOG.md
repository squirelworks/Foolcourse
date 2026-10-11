# Changelog

## 0.9.0

First release. Catalogs a courses folder and opens the selected book in Foolbook.

- Lists courses by subject and module
- Official list and extras. Overall score counts only the official list
- Opens the selected book in Foolbook on port 1337
- One viewer. The next Open replaces it instead of starting another
- Progress and a score per course, stored in an encrypted `.fcs`
- `--locale`, including `klingon`. Passed to Foolbook
- `--theme modern`
- Example modules: Street sense, Filing taxes
- Filing taxes ships best-effort `.tbk` shells. Not books the 8.1 engine would open
