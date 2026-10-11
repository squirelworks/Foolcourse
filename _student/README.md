# _student/

One file per student. The file is `.fcs`.

On disk it is encrypted. Extracted, it is this JSON:

```json
{
  "id": "student",
  "name": "Student",
  "courses": {}
}
```

Without the password the file cannot be extracted. This cut uses a
fixed password. A later module can replace it.

Default student is `student.fcs`. `--student alex` uses `alex.fcs`.
`courses` holds that student's progress and scores.
