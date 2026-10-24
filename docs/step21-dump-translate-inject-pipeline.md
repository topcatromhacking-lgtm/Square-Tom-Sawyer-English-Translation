# Square Tom Sawyer — v1.8 Script Pipeline (source-only)

## What has changed

We are moving away from sequential FCEUX-playthrough-led translation. The process is now **dump → match existing translation → edit TSV → encode → repack → patch**, followed by selective runtime QA.

**Verified indexed extraction:** 479 Bank 6 records in four groups, plus 41 Bank 8 events = **520 pointer-indexed records**. This is the ROM's known indexed script, **not yet every unindexed menu, dictionary, battle or item table**.

The v1.8 tool accepts exact original ROM `.nes` or `.zip`, SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`. It outputs a private editable TSV with the original pointer location, text offset, allocated bytes, partial Japanese glyph preview, source checksum, English translation, and approval flag. The output is **not intended for GitHub** because it contains original game script bytes and potentially third-party translation text.

### 1. Dump the script and carry forward the visually verified opening

```powershell
py -3 tools\script_pipeline_v18.py dump "C:\path\Square no Tom Sawyer (Japan).zip" --out work\script\master_PRIVATE.tsv --seed-opening
```

Optionally import previously downloaded BlackPaladin's script text files at the same time:

```powershell
py -3 tools\script_pipeline_v18.py dump "C:\path\Square no Tom Sawyer (Japan).zip" --out work\script\master_PRIVATE.tsv --seed-opening --script "C:\path\tomsawyer_script_000.txt" --script "C:\path\tomsawyer_script_001.txt" --script "C:\path\tomsawyer_script_002.txt"
```

The parser matches external drafts **by both original pointer-table address and text address**; unknown entries are reported separately. It never automatically approves external translations. For English line breaks inside the TSV, use literal `\n` in the English cell. Use `status=approved` only for reviewed text.

### 2. Calculate fit and candidate status

```powershell
py -3 tools\script_pipeline_v18.py report "C:\path\Square no Tom Sawyer (Japan).zip" work\script\master_PRIVATE.tsv
```

### 3. Build the cumulative patch from approved entries

```powershell
py -3 tools\script_pipeline_v18.py build "C:\path\Square no Tom Sawyer (Japan).zip" work\script\master_PRIVATE.tsv --out work\v18
```

This currently handles **Bank 8 indexed event windows** (0–11 and 12–40) and automatically preserves the verified v1.7 English font and overworld commands. It rejects overflows, non-ASCII/unmapped glyphs, excessive line lengths, altered ROM source rows, and any approved Bank 6 record. Bank 6 injection is **intentionally blocked pending dictionary/prefix analysis and robust bank allocation**. The script database already supports all 479 Bank 6 records, so further translation work need not await gameplay.

The first 12 entries are seeded from the visually verified English opening. Building the untouched seeded TSV creates an IPS that reproduces the **exact verified v1.7 patched ROM SHA-256** `5d869aa02c3c72cb06cefedd159e77f30d7cc18f630d7e1a4356ffaa94e7d34d`. Byte-for-byte it is the same resulting ROM, although the IPS binary is differently grouped (840 bytes rather than 868 bytes). Exact original-ROM rollback also passes.

### Current limitations and next engineering step

- Full inventory of **unindexed** battle texts, dictionary/phrase tables, items and UI is not complete.
- Large translated Bank 6 dialogue requires **safe relocation/ROM expansion**, not overwriting the next record.
- Visual line width, dictionary controls, and character-name prefixes need validation for each text context.
- No new v1.8 gameplay ROM has been FCEUX-tested. If you only seed the 12 confirmed event records, the output is **identical to v1.7** at runtime and does not require another playthrough.

**Next developer tasks:** classify Bank 6 record prefix/dictionary controls; locate all additional script tables; implement branch-safe allocator/expansion; bulk inject reviewed translations; then emulator test selected sample scenes rather than sequentially walk the whole game.

All produced IPS files and private TSV data stay under `work/`, which is ignored by Git. No Japanese ROM or historical third-party patches are included.