# v20 engineering — Bank 6 whole-bank text repacking

**2026-10-24 — Offline milestone, not a full-English release.**

The development process is now **dump → match existing drafts → approve/edit TSV → encode → repoint → IPS → selective FCEUX QA**. The previous sequential-screen workflow remains superseded.

## Verified original-ROM structure

The exact Japanese source ROM is 262,160 bytes, SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`, with MMC1/mapper 1 and 16 × 16 KiB PRG banks.

The indexed Bank 6 corpus contains **479 pointer records** divided into four groups (251 / 35 / 123 / 70) and exactly **14,325 allocated source bytes**, at file offsets `0x18812` through `0x1C006`. The end-boundary pointer is CPU `$BFF7` at file `0x18010`. Every validated record has a terminating `00`, and no original record contains an embedded `00` after its first two metadata bytes. The first two bytes are **copied verbatim** for every translation; their speaker/metadata semantics are not assumed solved.

The apparent 1,024-byte space between the pointer table and dialogue body, `0x18412..0x18811`, is **not vacant**: 899 of those bytes are nonzero in the original ROM. The short non-indexed tail `0x1C007..0x1C00F` is also populated. None of this is treated as available text storage.

## What v20 adds beyond v1.9

`tools/script_pipeline_v19.py` could replace short approved Bank 6 records only when **each record independently fit** within its original allocation. That made almost all of the longer English drafts impossible.

`tools/script_pipeline_v20.py` performs an **entire 479-record bank repack**:

1. Reads the exact original source ROM and the existing 520-record source-locked private TSV from v1.8.
2. For approved entries with original `00 00` metadata, preserves those two bytes, encodes English in the canonical Latin table, and emits `00` termination. Other records remain exactly as in the original.
3. Concatenates all **479 records**, preserving their sequence, and computes all 479 CPU pointers afresh from a contiguous Bank 6 allocation.
4. Preserves all `FFFF` group separators, the end-pointer sentinel `$BFF7`, source metadata, non-indexed data, ROM header and mapper. Only the recognized pointer words and `0x18812..0x1C006` data range may change.
5. **Fails closed** when the *combined* translated and untouched record data exceeds 14,325 bytes. There is no fake space, silent truncation or unsupported expansion.
6. Generates a single, cumulative IPS that includes already accepted v1.7 English opening/menu plus any approved Bank 8 edits; generates byte-exact rollback privately.

The **292 non-`00 00` header records** are conservatively blocked by default. The explicit `--allow-complex-header` option enables structurally preserved but **runtime-unverified** experiments; it is not an approval of those records' bytecode semantics.

## Real original-ROM verification

A disposable synthetic integration test modified exactly two Bank 6 dialogue bodies:

- Record 0 grows **7 → 8 bytes**.
- Record 1 shrinks **11 → 5 bytes**.
- Overall Bank 6 usage becomes **14,320 bytes**, leaving **5 bytes padding**.
- Record 0 stays at CPU `$8802`; record 1 moves to `$880A`; record 2 moves to `$880F`.
- **478 indexed pointers move**, while the four group divisions, all metadata prefixes, source end-pointer and other ROM areas remain intact.
- The forward IPS and reverse IPS reproduce exact original ROM SHA-256 on rollback.

This is a **structural relocation proof**, not confirmation of any Bank 6 NPC dialogue in FCEUX. Hardcoded or implicit references to relocated text, if any, still need runtime verification.

The approved opening-only TSV reproduces the already FCEUX-accepted v1.7 patched ROM SHA-256 `5d869aa02c3c72cb06cefedd159e77f30d7cc18f630d7e1a4356ffaa94e7d34d`. The entire current source/test snapshot passes **49 local unit and original-ROM integration tests** (previous 32 + 17 new). ROM-dependent tests skip in public source-only CI.

## Usage

From the repository root, using your own unmodified Japanese ROM:

```sh
python tools/script_pipeline_v18.py dump "/private/Square no Tom Sawyer (Japan).zip" --out work/script/master_PRIVATE.tsv --seed-opening
python tools/script_pipeline_v20.py plan "/private/Square no Tom Sawyer (Japan).zip" work/script/master_PRIVATE.tsv --out work/v20
python tools/script_pipeline_v20.py build "/private/Square no Tom Sawyer (Japan).zip" work/script/master_PRIVATE.tsv --out work/v20
python -m unittest discover -s tests -v
```

The build emits `work/v20/Square_Tom_Sawyer_Bank6_Repoint_v20.ips`, a rollback that **stays private**, and `manifest.json`. For actual translated content, the relevant TSV rows must be reviewed and marked `approved`. Avoid editing immutable original pointer/offset/record-hash fields.

**Never stack** v1.6/v1.7/v1.8/v1.9/v20 IPS files; each generator produces a single patch for the exact Japanese original.

## Remaining blocker — real full-script capacity

BlackPaladin's candidate inventory previously showed **374/479** main dialogue candidates longer than individual original allocations and an approximate **9,149-byte net increase** even at one byte per visible character plus termination (more with Bank 6's two-byte metadata and layout/control needs). Whole-bank repacking helps only when shorter records compensate for longer ones. It **does not make an additional 9+ KiB fit** in 14,325 bytes.

The next task is mapper-aware allocation/expansion research and interpreter/reference tracing. Merely appending new PRG data is **not** a proven MMC1-compatible solution for a ROM already containing 16 16-KiB PRG banks. Do not claim a completed expanded ROM until bank-switching changes and pointer consumers are mapped and emulated.

No ROM, patched ROM, full Japanese script, historical IPS binary, original Japanese glyph rollback data or third-party translation dump is committed to the public repository.
