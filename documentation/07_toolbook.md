# ToolBook

Foolcourse can open a ToolBook 8.1 `.tbk` because Foolbook can read one.
That is backward compatibility. It is not the format Foolcourse authors in.

## What the 8.1 books are

The course books that motivated this work are Click2learn ToolBook II
8.1 shells. A book is a `0xC00`-byte stub, then a stream at
`ZZZTBKBOOKLOC`: file offset `0xC00`, magic `0x22222222`. The stream
starts `03 4A 42 4F`, version `01 00 00 08`. Pages are `80 65` records.
OpenScript handlers are bytecode expanded by TB80CMP `FUN_1040_0970`.

Foolbook decodes that bytecode. It also compiles it back. The compiler
emits keyword tokens, CRLF, space runs, and repeats. It does not yet
emit back-reference compression.

## The shells

Foolbook can export a `.tbk`. The Filing taxes module ships nine of
them. A shell has:

- the locator at file `0x9EC`
- the JBO signature and version at `0xC00`
- a book-level property tree before the pages
- page records with `14 00 00 11` and bounds words taken from a live page
- a compiled `buttonClick` handler

Foolbook's reader opens these. The ToolBook 8.1 engine has not been
asked to. That is the next check, recorded in Foolbook
`plannedmilestones.md`.

What a live open still has to settle:

- whether the property tree is walked by length or by a count not yet found
- whether a minimal book needs the resource directory a real book has
- whether `go to page "P100"` is accepted, or the operand must be tokenized
- what `CDBSENDCREATE` and `FUN_12c8_0850` reject before they write bounds

The test is Win98, TB80RTM, break at the JBO check, open a Filing taxes
shell. The failure should be a specific check, not "not a book."

## Why this is here

So the lineage is written down, and so nobody mistakes a shell for a
finished book. Foolcourse does not need the 8.1 engine. A deployment
that has old `.tbk` files can open them. New courses are `.fbk`.

## Research notes (2026-10-14)

- RTM triage: UI/memory heavy, no named file open. See `tbworkingpapers/tbwp0018/rtm-triage.md`.
- RTM nameable: thin wrappers for BEGINPAINT, ENDPAINT, CREATEWINDOW, DESTROYWINDOW, SHOWWINDOW, ENABLEWINDOW, SETFOCUS, GETFOCUS, INVALIDATERECT, ENDDIALOG. See `tbworkingpapers/tbwp0018/rtm-nameable.md`.
- Object struct: 0x76 bytes, bounds at +0x0f, GDI handle at +0x3b, BitBlt flag at +0x1f. See `Foolbook/documentation/research-notes.md`.
