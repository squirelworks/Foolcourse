# .fcs

FCS is Foolcourse Student. `.fcs` is the student file. It is the standard.

It is not renamed JSON. On disk it is an encrypted envelope. Extracted,
it is a JSON object.

## Envelope

```
4 bytes   magic     FCS1
1 byte    version   1
16 bytes  salt
12 bytes  nonce
rest      ciphertext
```

The ciphertext is AES-GCM of the UTF-8 JSON. The associated data is the
magic `FCS1`. The key is PBKDF2-HMAC-SHA256 of the password, 32 bytes,
200000 iterations, using the salt in the file.

A file that does not start with `FCS1` is not an `.fcs`. A version other
than 1 is not this standard.

## Extracted JSON

```json
{
  "id": "alex",
  "name": "Alex",
  "preferred_name": "",
  "school_id": "",
  "cohort": "",
  "curriculum": "",
  "locale": "en",
  "theme": "",
  "port": null,
  "enrolled": "",
  "started": "",
  "last_seen": "",
  "courses": {}
}
```

| field | meaning |
| --- | --- |
| `id` | student id, stable |
| `name` | given name |
| `preferred_name` | what the window shows, if set |
| `school_id` | school or institution id, opaque |
| `cohort` | class, section, or intake |
| `curriculum` | official list this student is on |
| `locale` | Foolcourse locale id, such as `en` or `klingon` |
| `theme` | `classic` or `modern`, empty means the default |
| `port` | viewer port, or null |
| `enrolled` | date added, ISO |
| `started` | first open, ISO |
| `last_seen` | last open, ISO |
| `courses` | one record per course id |

A course record may hold `opened`, `completed`, `completed_on`,
`attempts`, `time_seconds`, `last_page`, `visited`, and `score`.
`score` may hold `correct`, `answered`, `percent`, `best`.

## Password

The password is not in the file. The opener recovers it. Without it the
file cannot be extracted. A later module may replace the password. It
must not change this envelope.
