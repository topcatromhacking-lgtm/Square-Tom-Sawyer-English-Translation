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

## v1.9 — guarded Bank 6 bulk injection (2026-10-24)

The script-first workflow now supports **in-place injection of multiple approved Bank 6 translations** as well as the 41 Bank 8 event records. The source inventory proves that **187/479 Bank 6 records have original `00 00` leading metadata**, with another **292 complex-header records** requiring further interpreter research. Version 1.9 intentionally preserves those two metadata bytes, original record allocation, all Bank 6 pointers and unapproved strings. It refuses English that overflows, contains unsupported glyphs or has a complex/unknown header. It does not automatically accept translated text from third parties.

**Offline evidence:** 32 local tests passed (20 from v1.7–v1.8 plus 12 for v1.9); exact Japanese original ROM identity, bounded synthetic-record edit, cumulative v1.7 opening/menus, and original-SHA256 rollback verified. A 12-approved-opening-only TSV regenerates the exact previously FCEUX-approved v1.7 patched ROM. **No new Bank 6 dialogue has yet been visually verified in FCEUX.**

Start with `python tools/script_pipeline_v19.py audit ORIGINAL.zip [TSV]`; to build with explicitly approved short translations use `python tools/script_pipeline_v19.py build ORIGINAL.zip work/script/master_PRIVATE.tsv --out work/v19`. The resulting IPS is a **standalone cumulative patch** from the original Japanese ROM. [Engineering notes](docs/step22-bank6-inplace-v19.md).

**Next blocker:** a controlled allocator / MMC1-compatible expansion architecture for longer English translations and verified decoding of the 292 complex-header records. We continue with dump/translate/inject—not sequential gameplay-driven translation.

## v20 engine — whole-bank script repacking (2026-10-24)

**New verified offline capability:** `tools/script_pipeline_v20.py` rebuilds all **479 Bank 6 indexed records** into the same original 14,325-byte allocation, using approved translations from the private v1.8 TSV. A record can now **grow beyond its old individual allocation if other records shrink**. It repoints the complete indexed table, preserving the original two-byte record metadata, pointer order, `FFFF` group delimiters, end-pointer sentinel, non-indexed data, MMC1 header and ROM size.

On the real Japanese source, a disposable synthetic 7→8 and 11→5 byte test moved **478 indexed pointers** and left five bytes spare. Source-verified cumulative forward/rollback passed; a no-Bank6-change build reproduced the exact previously accepted v1.7 patched ROM SHA-256. **49 local tests PASS, 17 new in v20.** No new Bank 6 dialogue has been visually tested in FCEUX.

This is **not** full-ROM expansion or full English text reinsertion. Combined Bank 6 capacity remains **14,325 bytes**; the extensive English drafts exceed it by approximately 9+ KiB. Non-`00 00` metadata record edits remain blocked by default and can only be attempted with an explicit experimental override. Runtime hardcoded references are still to be mapped.

[Engineering notes](docs/step23-bank6-full-repack-v20.md). The source-only v20 package includes the script pipeline and unit tests; it does not contain copyrighted ROM data.

### v20 dictionary-capacity investigation (2026-10-24)

A second, read-only engineering result changes our next technical priority: the 478 publicly available Bank 6 English draft strings from BlackPaladin2022 are **22,996 ASCII characters**. A greedy nested **DTE/pair-dictionary** feasibility simulation suggests the entire corpus *might* fit the original 14,325-byte Bank 6 allocation **without a mapper upgrade** if an adequate decompressor can be implemented.

At **160 dictionary tokens**, the optimistic modeled size is **13,319 bytes**, leaving **1,006 bytes** before linebreaks and other omitted costs; at **176 tokens**, it is **12,996 bytes** (1,329 bytes margin). At 128 tokens it barely fits (267 bytes margin). These estimates include two leading metadata bytes and a terminator for every one of 479 records; **they do not include** a game decoder, dictionary table/stack, reserved token code verification, wrapping, explicit linebreaks or other control codes. This is **NOT** a working compressed ROM or assurance it will fit.

The **next milestone is reverse-engineering the original text-byte consumer and safely adding a dictionary expansion step**, evaluating reserved codes and RAM/ROM table storage before changing MMC1. If that approach fails its real constraints, return to mapper-aware expansion.

[Detailed DTE feasibility audit](docs/step24-dte-feasibility-v20.md) · `tools/dte_capacity_v20.py` · `tests/test_dte_capacity_v20.py`. **55 local tests now PASS (49 preceding + 6 new dictionary-estimator tests).** The published source files are analyzed as private inputs; no third-party translated script is copied into this repository.

## v21 — Native reference decoding and flat dictionary feasibility (2026-10-24)

**Major ROM-engineering discovery:** The original fixed-bank text reader already handles **`03 index` embedded text references** through CPU `$EDC2–$EE4F`. The verified source contains **237 references from 172 dialogue records to 29 shared entries**. Those referenced phrases have no nested `03` references. Treat the first 29 source entries as **shared dependencies**, not independent safe-to-overwrite strings.

A flat **single-level** phrase dictionary simulation over BlackPaladin's 478 existing English Bank 6 drafts is more encouraging than the former nested DTE estimate. At **160 tokens**, English symbols + the original 479 headers/terminators are estimated at **12,512 bytes** (1,813-byte margin within Bank 6's 14,325 bytes). Modeling the dictionary as NUL-terminated phrases plus 16-bit indexes gives approximately **1,046 bytes**, potentially fitting the original **1,160-byte zero-filled Bank 5 tail** (`0x17B88–0x1800F`). See [v21 detailed source audit](docs/step25-native-reference-and-flat-dictionary-v21.md).

**This is not a functioning ROM compression system.** Only 90 byte values are unused in untouched original Bank 6 body data (some reserved), so a 160-token namespace cannot simply be assigned. Bank 5/6 switching, 6502 decompression code, true line/control costs and mixed-script compatibility must be resolved. No new IPS has been released or FCEUX-confirmed for v21.

Read-only audit and lossless simulated flat dictionary: `tools/native_dictionary_v21.py`. Regression tests: `tests/test_native_dictionary_v21.py`. **67 local tests PASS** (55 previous + 12 new); all external script text remains private.

**Next engineering gate:** prove one safe token-dispatch hook and dictionary access while preserving the original `03` indirection and the known-good English opening/menus. Only then automate whole-script compression and injection.

## v22 — Native reference proof and fixed-bank hook survey (2026-10-24)

**Offline diagnostic milestone:** The original game supports `03 index` native phrase references. A new checksum-guarded builder, `tools/native_reference_probe_v22.py`, replaces one existing duplicate literal in `B6-420` with native `03 01`, preserving the original two-byte record prefix and 7-byte allocation. Its abstract text expansion is exactly identical to the original, **no Bank 6 pointers move**, four additional bytes change versus the accepted v1.7 ROM, and its private rollback restores the exact original image. The cumulative diagnostic IPS is generated locally and is not required for translation progress.

**Important limitation:** The conservative no-nesting/no-controls scan found only **one qualified duplicate**, so the existing two-byte native reference system cannot replace a custom 160-token single-byte decoder. `tools/decoder_hook_survey_v22.py` establishes original text-reader call sites but **does not identify a safe executable cave** in the fixed bank; zero and FF runs are structured data.

**81 local regression tests PASS** (67 prior + 14 v22); no FCEUX test of the new native reference has been performed. Source code and tests: `tests/test_native_reference_probe_v22.py` and `tests/test_decoder_hook_survey_v22.py`. [v22 report](docs/step26-v22-native-probe.md).

**Next:** prove a safe original-ROM decoder hook location and dictionary accessibility, then implement a genuine one-byte English phrase token and build the translator around the script database. Do not ask the user to replay the game one screen at a time.

## v23 — Experimental 29 genuine single-byte tokens (2026-10-24)

**New binary milestone (offline PASS; FCEUX pending):** Source-pinned `tools/native_onebyte_tokens_v23.py` rewrites the original $03,index control to one-byte **D0–EC** native phrase references without adding new executable code. Two short in-place fixed-bank 6502 edits (4 bytes at CPU `$EDE7`; 9 bytes at `$EDFD`) transform all **237** original native references across 479 indexed Bank6 records. The original Japanese bodies never use D0–EC as ordinary source glyph bytes, excluding reference operands.

The builder repacks Bank6 and recalculates 479 source pointers (**445 actually change**). Text bytes fall **14,325 → 14,088**, recovering **237 real bytes** within the original bank. An independent logical expander matches **all 479 source records**, retaining metadata, FFFF separators and original source ROM dimensions. The new standalone cumulative IPS also preserves v1.7's FCEUX-accepted English opening and LOOK/TAKE/DIG/ITEM interface. Exact source-ROM rollback PASS. **95 local tests PASS** (previous 81 + 14 v23).

**Not yet emulator-tested or production-ready:** possible non-indexed Bank6 source references, binary interpreter state and gameplay progression need FCEUX verification. This provides only the original **29 shared phrases**, not the 144–160 new English dictionary entries needed for full translation. The remaining Japanese dialogue is still untranslated.

See [v23 code](tools/native_onebyte_tokens_v23.py), [tests](tests/test_native_onebyte_tokens_v23.py), and [technical report](docs/step27-v23-onebyte-tokens.md). Use the v23 patch **alone** on the clean original ROM; never stack IPS versions.

## v24 — Read-only FCEUX Bank 6 token execution trace (2026-10-25)

**User confirmation:** v23 successfully boots and still displays the English introduction. This establishes **v23 boot + Bank 8 English intro PASS**, **not** Bank 6 one-byte token execution: the 12 translated opening records are Bank 8.

To avoid asking for an extended playthrough, `tools/fceux_v24_token_trace.lua` is a new **read-only observer**. It fingerprints the exact fixed-bank v23 decoder bytes, monitors `$EDE7` text dispatch, `$D0–$EC` token candidates, `$EDFD` token resolver, and `$EE2C` shared-text reader, shows counters onscreen, and writes `SquareTomSawyer_v24_token_trace.txt` where possible. It does **not** mutate game memory or savestates, load another ROM, or create a new IPS. The user may trigger just one nearby LOOK/NPC response; no line-by-line gameplay is needed.

The local project passes **98 regression tests** (95 previous + 3 v24 tests). A simulated Lua/FCEUX callback test verifies the trace report; **real FCEUX token-execution evidence is still pending**. [Instructions and interpretation](docs/step28-v24-runtime-trace.md).

**Next gate:** first confirmed Bank 6 token dispatch/resolver execution (and rendered text), then extension of the 29-entry single-byte dictionary and automated compressed English script injection.

## v24b — FCEUX tracer fingerprint correction (2026-10-25)

A user-uploaded v24 trace ran **9,390 frames** but reported `Expected v23 at $EDE7, got $00`, all counters zero, and `WRONG ROM / PATCH`. This is **inconclusive**, not proof of a bad ROM: v24 checked CPU memory only once, at script startup, and then suppressed every hook after that one failed check.

The original **v23 IPS bytes are independently verified**: on the SHA-256-matched Japanese game, they correctly produce the expected interpreter edits `C9 D0 90 06` at ROM offset `0x3EDF7` and `38 E9 CF 85 F1 A9 00 85 F2` at `0x3EE0D`. Whether the user's emulator loaded those edits remains unknown.

**Use `tools/fceux_v24b_token_trace.lua` instead of v24.** It independently checks `rom.readbyte` (physical cartridge data) and `memory.readbyte` (currently mapped CPU memory), **repeats the check every 60 frames**, and reports original, v23, unmapped and unavailable states separately. It writes `SquareTomSawyer_v24b_token_trace.txt` and can be launched at the user's **current gameplay position**. No new IPS, restarting the game, or sequential playthrough is required.

Four new local read-only/mocked-emulator scenarios pass, including initial CPU zeros with correct cartridge patch and actual unpatched ROM. **Bank 6 token runtime remains unconfirmed.** [v24b diagnosis and test](docs/step29-v24b-fingerprint-diagnostic.md).

## v24b — Live Bank 6 one-byte token path PASS (2026-10-25)

The user returned a real FCEUX `SquareTomSawyer_v24b_token_trace.txt`: **both physical ROM and mapped CPU match v23**, **107 Bank6 dispatches**, **2 single-byte token candidates and 2 resolver executions**, **21 secondary-reader execution events**, **zero unexpected high input bytes** over **7,032 frames**. Tokens **D1 → B6-001** (frame 6117) and **DD → B6-013** (frame 6765) both reached the patched token resolver. This establishes **actual Bank6 experimental 6502 one-byte token path execution**, resolving the earlier false-negative v24 startup fingerprint.

**Scope matters:** these are 2 runtime examples among 237 converted native references. The trace itself does **not** prove visually correct Japanese text expansion for every path, nor does it implement or validate a 160-entry English dictionary. Visual fidelity and bulk English dictionary allocation remain open. Do **not** ask user to replay the startup diagnostic. [Full accepted trace and next engineering gate](docs/step30-v24b-live-token-execution.md).

## v25 same-bank dictionary feasibility (2026-10-25)

The user's v24b FCEUX log has **confirmed actual v23 Bank6 D1/DD token and resolver execution**. This allows us to stop running basic decoder-startup diagnostics.

A newly examined storage strategy may simplify full English injection: **pack the compressed English dialogue *and* its separate phrase pointer table/data into Bank6**, instead of depending on Bank5 while Bank6 is active. The v21 optimistic 160-token data estimate becomes **12,512 bytes of text + 320-byte pointer table + 726-byte phrase bodies = 13,558**, leaving **767 bytes** inside Bank6's original 14,325-byte indexed text allocation. At 144/176 tokens, modeled margins are 554/1,021 bytes.

This is a **capacity hypothesis, not a ROM decoder**. The existing v23 29-token routine still resolves its phrases through the **original first group**, not a separate dictionary pointer base; safe 160-code namespace and control/linebreak overhead remain unresolved. `tools/same_bank_dictionary_layout_v25.py` supplies bounds checks and `tests/test_same_bank_dictionary_layout_v25.py` source-only tests for the proposed allocations. [Engineering constraints and next implementation gate](docs/step31-v25-same-bank-dictionary-layout.md).
