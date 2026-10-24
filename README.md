# Square Tom Sawyer — English Translation

Source-based English translation of **Square no Tom Sawyer** (Square, Famicom/NES, 1989). **Development in progress; no full playable English release yet.**

## Verified original ROM

- File: `Square no Tom Sawyer (Japan).nes`
- Mapper: MMC1 (mapper 1), 256 KiB PRG, CHR-RAM.
- Full file: 262,160 bytes; CRC32 `AEA5B066`.
- SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`.
- Main dialogue bank: **479 verified indexed records**, four pointer groups, 14,325 encoded source bytes. Additional story, UI and event strings lie outside that bank.

## Prior work

The v1.1 proof-of-concept renders `AMERICA / MISSOURI / ONE NIGHT, 1855` correctly in FCEUX, but its replacement font makes untranslated Japanese dialogue unreadable. Both earlier translation IPS files use the same approach of replacing original Japanese bitmaps with Latin glyphs and re-encoding text; they do not introduce a bilingual font switch. Our objective is **a complete English-language game**, not bilingual display during partial builds.

Two predecessor patches were separately audited against the exact Japanese source ROM:
- `TOMSAWEE.IPS`: 3,123 changed bytes; Latin A–Z at `5E–77`.
- `Square NTS Translation 2.0.ips`: 2,333 changed bytes; Latin A–Z at `6E–87`.

Do **not** stack those two IPS files. See [historical forensic report](docs/step15-historical-ips-forensics.md). Scripts from [BlackPaladin2022/Dumped-Scripts](https://github.com/BlackPaladin2022/Dumped-Scripts) are an external research and translation reference, not redistributed here.

## Repository structure

- `tools/`: source identity, exact text extraction/repack, font experiments, predecessor IPS analysis, and v1.4 master script tooling.
- `tests/`: Python standard-library regression tests.
- `docs/`: reports, glyph lookup and roadmap.
- `patches/`: reproducible ASCII-hex format for our v1.1 proof-of-concept only (not ROM images).
- `work/`: **ignored** local output including extracted script and private translation comparisons.

## How to use

```bash
python -m unittest discover -s tests -v
python tools/analyze_rom.py "/private/Square no Tom Sawyer (Japan).zip" --out work/inventory
python tools/build_master_inventory_v14.py "/private/Square no Tom Sawyer (Japan).zip" --script "/private/tomsawyer_script_000.txt" --script "/private/tomsawyer_script_001.txt" --out work/v14
```

**v1.4 update (2026-10-24):** The first two public BlackPaladin text files contain 481 pointer headers, of which two are `FFFF` delimiters rather than real records. The remaining **479 valid pointer references** match the four verified groups. Preliminary one-byte capacity analysis finds **478 English candidates, with 374 exceeding their current record allocations** (at least **10,070 bytes** of positive per-record overflow). See [capacity snapshot](docs/v14-capacity-snapshot.md). These are lower bounds, not final encoded sizes.

## Next milestones

**v1.4:** reconcile the 479 verified ROM records with historical IPS changes and BlackPaladin's external translated script; calculate source capacity and conservative English overflow. Then implement one canonical English encoder, safe pointer relocation, and if necessary MMC1 ROM expansion. Prioritize a continuous playable first quest before full-game QA.

The original Japanese ROM, extracted original dialogue, historical IPS binaries, patched game images and saved games are **never committed**.

## Origin and acknowledgments

The older reverse-engineering experiments v0.1–v1.3 are preserved in the private [romhacking incubator](https://github.com/topcatromhacking-lgtm/romhacking/tree/main/projects/square-no-tom-sawyer-nes). The working knowledge and tested source files are migrated here. Previous English translation work by the archived patch authors and BlackPaladin2022 should be credited in any release; archive metadata alone is insufficient to conclusively attribute both binary patch files to named authors.

## v1.5 — English encoder and bounded relocation (2026-10-24)

**Source-only milestone complete:** `tools/english_codec_v15.py` implements verified historic English A–Z codes `6E–87`, original numeral codes `10–19`, space `8F`, LF `01`, and record end `00`. Punctuation is explicitly provisional pending visual FCEUX confirmation. Unsupported glyphs, unexpected line lengths and hidden data loss fail loudly.

`tools/relocate_dialogue_v15.py` repacks **whole encoded records** within an exact source-verified PRG-bank-6 pointer-group window, rewrites only the window's indexed pointers and data bytes, and rejects overflow, absent terminators, cross-group changes or invalid original checksum. The original ROM was used offline to test a one-byte relocation, successfully moving a pointer from `$8814` to `$8815`. This is structural verification—not FCEUX gameplay confirmation or cross-bank expansion.

**63 source-free Python regression tests passed locally (46 prior + 17 new).** New source and tests are committed; no modified commercial game image or third-party patch data was uploaded. See [v1.5 engineering notes](docs/step17-encoder-relocator.md).

**Next:** classify dictionary/prefix metadata and runtime pointer references, then build an actual contiguous English first-quest slice, followed by safe out-of-bank allocation/mapper feasibility analysis for the larger dialogue overflow.

## v1.6 — English opening cutscene test (2026-10-24)

The source-verified **v1.6 forward IPS now exists**. It translates twelve consecutive opening event records (the river/ticket conversation and Tom waking), and relocates ten pointers in bank 8 while retaining the original 333-byte allocation. New English text consumes 324 bytes and leaves 9 bytes free. Eleven regression tests and original-ROM forward/exact-reverse verification PASS **offline**.

The important punctuation correction is apostrophe=0x88, question mark=0x8D (these were reversed in v1.5). The A–Z layout remains 0x6E..0x87. The v1.6 builder is `tools/build_opening_v16.py`; guards and tests are in `tests/test_opening_v16.py`; [technical notes](docs/step18-opening-v16.md).

**FCEUX test pending:** use the standalone v1.6 IPS against the exact clean Japanese original. Verify opening and first exchanges; do not save or expect untranslated later Japanese text to display correctly. This is NOT the complete first-quest release, and the larger script expansion remains outstanding.

## v1.6 FCEUX PASSED; v1.7 English overworld commands ready (2026-10-24)

User screenshots confirmed the English river dialogue, multiple portraits, correct line breaks, Tom's waking scene and successful transition into outdoor/indoor gameplay. **v1.6 is visually accepted for the submitted sequences**, not every possible intro route.

The command menu remained Japanese. Investigation identified **fixed-bank direct-CHR tile arrays** rather than indexed dialogue strings. `tools/build_overworld_menu_v17.py` now constructs an original-ROM-only cumulative **v1.7 standalone IPS**: v1.6 dialogue plus **LOOK, TAKE, DIG, ITEM** at ROM offsets 0x3D1AF, 0x3D1B6, 0x3D1BF, 0x3D1C8. Only 16 additional bytes differ from the v1.6 patched ROM. Local forward/rollback identity PASS, forward IPS 868 bytes; eight menu tests PASS. **v1.7 FCEUX confirmation pending.**

See [v1.7 technical documentation](docs/step19-overworld-menu-v17.md). Do not stack v1.6 and v1.7 IPS files; use v1.7 by itself on the original Japanese game. Next: test all four menu labels and interactions, then extend into inventory, NPC and battle vocabulary.

## v1.7 FCEUX validation (2026-10-24)

**User confirmation:** all four overworld commands **LOOK, TAKE, DIG, ITEM** appear translated correctly in the emulator; user reports "All good." **v1.7 menu translation PASS.** This confirms the direct-CHR text representation and combined v1.6 + v1.7 patch rendering. The report does not independently establish all command submenus, action result messages, item handling, or battles; those remain untested/partially Japanese.

**Next milestone v1.8:** focused vertical slice covering the actual LOOK/TAKE/DIG interaction results and ITEM submenu, with cumulative reversible original-ROM-only IPS and first-quest path checks. Then prioritize battle UI and dialogue/relocation. See `docs/step20-v17-accepted-v18-plan.md`.

## Revised workflow — dump, translate and inject (2026-10-24)

**User-directed correction:** development is not a sequential gameplay translation of LOOK/TAKE/DIG results, town screens, battles and NPCs one by one. Instead, follow the conventional scalable ROM-hacking workflow: **extract scripts -> align published translations -> edit/approve -> encode -> repoint/expand -> inject in bulk -> QA representative scenes -> full playthrough**.

A v1.8 source-only script-pipeline prototype has been packaged for the user. It SHA-validates the exact Japanese ROM, exports **520 verified indexed records** (479 PRG bank 6; 41 PRG bank 8), matches draft translations from locally provided BlackPaladin scripts by both original pointer-field and text offset, emits a private editable TSV and diagnostics, and generates cumulative reversible IPS files from approved Bank 8 entries. With the 12 verified opening records seeded, it reproduces the **exact same v1.7 patched game image** (SHA-256 `5d869aa02c3c72cb06cefedd159e77f30d7cc18f630d7e1a4356ffaa94e7d34d`) while building a differently grouped 840-byte IPS. **20 local regression tests PASS.**

Important limitations: the 520 records are **not yet every string in the game**, and PRG bank 6 injection is **disabled intentionally** until its dictionary/prefix conventions and cross-bank allocation are proven safe. More unindexed UI, battle and item tables must be discovered automatically before claiming a complete script dump. See [the v1.8 pipeline guide](docs/step21-dump-translate-inject-pipeline.md).

**The next engineering work is script coverage and a safe full-bank allocator, not asking the user to play dialogue screens.** FCEUX is reserved for selected smoke tests and final QA.
