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
