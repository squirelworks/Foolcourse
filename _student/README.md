# _student/

One file per student. Plain JSON. No lock, no password. A later module
can make this secure. For now it is the record Foolcourse and Foolbook share.

Default student is `student.json`. `--student alex` uses `alex.json`.

```json
{
  "id": "student",
  "name": "Student",
  "courses": {}
}
```

`courses` is the progress and score store: opened, last page, quiz answers.
