# Formats

## .fcs — Foolcourse Student

An envelope. On disk it is sealed. Extracted, it is JSON.

Foolversity writes it. Foolcourse and Foolbook each open it with their
own code. The password is a placeholder for a small deployment. A later
module replaces it. Do not treat it as security.

A student record holds the identity Foolversity was given (id, name,
school, cohort) and, once courses are opened, the progress Foolbook
writes: pages visited, last page, quiz answers, best percent, completed.

## .curriculum.json

Names a curriculum and its official list.

```json
{
  "name": "Money",
  "official_name": "Filing taxes",
  "official": ["do_i_file", "papers", "deduction"],
  "extras": [],
  "root": "_courses",
  "notes": ""
}
```

`official` is the list that counts toward the overall. Anything else
found in the courses folder is extra, whether or not it is named in
`extras`.

## .school.json

Foolversity only. An id, a name, the curricula it offers, the students
it has. Foolcourse does not read it.

## .fbk / .fsk

Foolbook's own books. A 4-byte magic (`FBK1` / `FSK1`), a flags byte,
then JSON. Bit 0 means zlib-compressed. `.json` is the working copy.

## .tbk / .sbk

ToolBook 8.1 books, read for backward compatibility. Foolbook decodes
OpenScript handlers from these. It can also write a best-effort `.tbk`
shell. That shell is not a book the 8.1 engine has been shown to open.
See [07_toolbook.md](07_toolbook.md).
