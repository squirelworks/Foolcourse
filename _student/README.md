# _student/

One file per student. FCS is Foolcourse Student. The file is `.fcs`.
The standard is `progress/FCS.md`.

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
