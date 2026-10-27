# Step 36 — v27 first English visual PASS and v28 bulk translation audit

**2026-10-26. Visual milestone accepted from user screenshot.**

## What is now proven end-to-end

The user supplied a FCEUX screenshot of the exact B6-356 translation:

```
THE ANGEL WHISPERED.
THERE'S NOTHING
FOR YOU HERE.
```

The screen shows three distinct, readable, uppercase English lines inside the game's lower dialogue window, including proper apostrophe, full stops, letter spacing and vertical line spacing. There is no visible clipping or corrupted glyph. This confirms the earlier v27 runtime trace's **six of six English token/independent-pointer matches** did indeed lead to correct displayed English. **v27 Bank6 token → independent dictionary → font/renderer → on-screen text is ACCEPTED.** Do not request further single-line decoder smoke tests.

## Larger-script feasibility: materially changed by wrapping

The two public `BlackPaladin2022/Dumped-Scripts` files under `(NES) Square no Tom Sawyer MIX` contain English draft text for **478 of 479 indexed Bank6 script records**, with **22,996** visible ASCII characters before normalization. A deterministic English word-wrap at 20 characters (the maximum phrase length explicitly exercised in the visual pilot, not a proven absolute renderer width) yields:

| Wrapped lines per entry | Entries |
| --- | ---: |
| 1–2 | 194 |
| 3 | 109 |
| 4 | 83 |
| 5+ | 92 |
| Missing | 1 |

Therefore **175 drafts** exceed the three-line pilot and need verified game paging/continuation semantics. The wrapped draft corpus requires **976 linebreak positions** in addition to letters and spaces. These counts are **planning estimates**, not approved English edits or a patched ROM.

An independent fresh **nonnested English flat-phrase** estimate disallowing tokens that straddle actual linebreaks, with **160 tokens**, yields:
- **13,839** encoded symbols including literal linebreaks.
- **1,437** bytes of two-byte record metadata and one terminator across 479 records.
- **320** dictionary pointer bytes.
- **510** NUL-terminated phrase-body bytes.
- **16,106** bytes in all, compared to the original **14,325-byte** indexed Bank6 text allocation.
- **1,781-byte modeled shortfall**, not counting unclassified original controls, native paging or extra engine machinery.

This invalidates the prior 160-token **767 bytes free** estimate, which came from unwrapped source. It is a heuristic feasibility result, not proof that every possible codec necessarily overflows. A controlled multi-bank text storage/mapper architecture should be developed rather than silently shortening translations to force them into the original bank.

## Original ROM control audit

Source-ROM SHA-256: `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`.

Of the 479 indexed Bank6 records:
- **237** genuine native `03 index` source references, with the one-byte operand excluded from control counting.
- **529** direct `01` bytes and **107** direct `02` bytes in the stream after skipping `03` operands.
- **292** records have non-`00 00` two-byte metadata prefixes.
- Byte values `04..0F` also occur in text bodies but **cannot automatically be labeled controls**; some may be native character codes.

These measurements caution against naively replacing the entire Japanese record with ASCII English and losing its original dialogue presentation grammar.

## v28 source-locked bulk importer

The accompanying **source-only** `bulk_script_audit_v28.py` in the downloadable package provides: source SHA gating, automatic opt-in download of the two published draft files (or local file input), exact `ptr_at`/`text_at` alignment via existing v18 master pipeline, a **private editable 520-row TSV**, per-record wrapping/potential continuation estimates and native-metadata/control flags. All original Japanese record bytes and prior v1.6 approved English opening records remain represented. No Japanese ROM, historical IPS or third-party full translation text is shipped with the package.

The full local **v27+v28 subset suite passes 25 tests**, including ROM-gated native-control checks, source-locking, English word-wrap invariants, and an end-to-end synthetic 479-entry import that never uses vendor text.

### Command on a network-enabled PC

```powershell
py -3 tools\bulk_script_audit_v28.py "C:\path\Square no Tom Sawyer (Japan).zip" --download-public-drafts --out work\v28_private
```

Private output: `sts_v28_translation_master_PRIVATE.tsv`, `sts_v28_dialogue_review_PRIVATE.tsv`, `sts_v28_layout_audit.json`.

This is an **import, audit and integration engineering checkpoint**, not a new translation IPS. The ROM/mapper expansion design and true pagination engine still need reverse engineering before a complete bulk-patched ROM can be FCEUX accepted.

## Next concrete engineering stage

Implement a source-verified **native pagination state machine** for long records, then a mapper-compatible multi-bank script allocator (rather than assuming Bank6 can hold full English). Keep a reversible original SHA-pinned build, preserve all 479 primary record identities and all 41 Bank8 indexed event scripts, and verify a small set of representative long dialogues. Avoid sequential line-by-line gameplay translation.
