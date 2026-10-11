# _courses/

Books Foolcourse catalogs and Foolbook opens.

The example is `Getting around/Street sense/phone`: how to not walk
while using your phone. Open it with Foolbook:

```bash
python3 /path/to/Foolbook/foolbook.py "_courses/Getting around/Street sense/phone.fbk"
```

A course may have a locale overlay: `<id>.<locale>.json` beside the book.
Foolbook applies it when launched with `--locale`. `phone.klingon.json` is the first.
Missing overlay leaves the course as written.
