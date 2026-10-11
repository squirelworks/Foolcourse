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
  "courses": {}
}
```

| field | meaning |
| --- | --- |
| `id` | student id, stable |
| `name` | display name |
| `courses` | one record per course id |

A course record may hold `opened`, `completed`, `last_page`, `visited`,
and `score`. `score` may hold `correct`, `answered`, `percent`, `best`.

## Password

The password is not in the file. The opener recovers it. Without it the
file cannot be extracted. A later module may replace the password. It
must not change this envelope.
