# v1.4 — Master script and relocation inventory

## Inputs and scope

`tools/build_master_inventory_v14.py` accepts the SHA-256-pinned original Japanese iNES image, or a ZIP containing it, plus zero or more locally obtained BlackPaladin script text files. All source-derived script text and candidate English lines are written to **ignored local `work/` output**, never GitHub.

The confirmed main dialogue pointer table has **479 records** grouped into 251, 35, 123 and 70 entries (14,325 total source bytes). This is **not** an inventory of all the game's battle, menu, NPC or event text across PRG banks.

## Why BlackPaladin's first two scripts show 481 entries

BlackPaladin's public `tomsawyer_script_000.txt` contains 411 pointer headers and `tomsawyer_script_001.txt` contains 70, giving 481. The original ROM instead has two `FFFF` group markers at **pointer-table file offsets `0x1820A` and `0x18252`**. BlackPaladin includes them as uncertain text references pointing to `0x2000F`. Both are intentionally reported as `GROUP_DELIMITER_FFFF`, not treated as translated game strings.

After excluding them, the external scripts have **479 unique references for exactly 479 valid pointer-table offsets**. This is a *pointer-field coverage check*, not yet proof that every listed string offset and candidate translation agrees with the original ROM. The v1.4 tool additionally requires an exact pair of pointer-table offset and string file offset for each record; mismatches and duplicates are quarantined for manual review.

## Output columns

`work/v14/master_script_PRIVATE.tsv` includes stable index, group, pointer location, original CPU pointer and text offset, allocated record length, maximum original payload length, external candidate text, and provisional byte counts.

`minimum_one_byte_requirement` is **only a lower bound**: one byte per visible candidate character, plus a terminal `00`. It does **not** implement the final English code map, punctuation, explicit linebreaks, screen-width constraints, word wrapping, accents, dictionary expansion or relocation. `minimum_overflow_bytes` is likewise an early triage indicator—not an authorized ROM edit.

`work/v14/unmatched_references_PRIVATE.tsv` captures the two separators plus any other pointer/text offset mismatch or duplicate. `work/v14/summary.json` contains aggregate results without translation text.

## Usage

Obtain the original Japanese ROM legally, then download the two BlackPaladin source references from the [public script repository](https://github.com/BlackPaladin2022/Dumped-Scripts/tree/main/%28NES%29%20Square%20no%20Tom%20Sawyer%20MIX) to a private local folder. For an initial Bank 6 census, only `_000` and `_001` are needed; `_002` covers a **different** event/intro script bank and must be inventoried separately.

```sh
python -m unittest discover -s tests -v
python tools/build_master_inventory_v14.py "/private/Square no Tom Sawyer (Japan).zip" \
  --script "/private/tomsawyer_script_000.txt" \
  --script "/private/tomsawyer_script_001.txt" \
  --out work/v14
```

The local source-ROM-only run passed: **479** validated records across four groups. Five new v1.4 source-free unit tests passed, and an integrated local project snapshot passed **46 total tests**. The external-script candidate lengths still need a full local run with the actual script text files.

## Next stage

1. Identify and verify **one** canonical Latin glyph table (historical Translation 2.0 A–Z at `6E–87` is a reference, not a complete punctuation encoder).
2. Add a deliberate control-code grammar and line-width limits for each text context.
3. Measure true encoded byte requirements for candidate English lines.
4. Implement relocation with guarded pointer updates; use mapper-aware ROM expansion only when required.
5. Build and test a continuous first-quest English beta, retaining proper attribution for source translations.

Do not stack historical patches or reuse overwritten original record terminators without validating the engine's string boundaries.
