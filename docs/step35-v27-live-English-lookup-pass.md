# Step 35 — v27 live English phrase dictionary lookup PASS

**2026-10-26 — User FCEUX report** `SquareTomSawyer_v27_english_phrase_trace.txt` submitted and reviewed.

## Accepted runtime evidence

The report identifies the exact v27 physical cartridge and monitors 8,553 FCEUX frames. The corrected helper witness validates **all six English token calls at actual Bank6 execution time**, with no wrong-bank helper execution and no returned-pointer mismatch.

| Evidence | Observation |
| --- | --- |
| Physical cartridge | v27 verified |
| Bank6 text dispatches | 53 |
| New English token hits (ED/EE/EF) | **6** |
| Actual BF0A Bank6 helper byte matches | **6** |
| Independent dictionary lookup pointer matches at EE1C | **6** |
| Wrong/foreign-bank helper executions | **0** |
| Pointer mismatches | **0** |
| Secondary-reader execution events | 102 |
| Frames | 8,553 |

The report labels its aggregate token count `Tokens D0-ED observed: 6`, but its instrumentation actually enumerates and counts **D0 through EF**; all observed six belong to the three new English tokens.

The exact execution sequence was encountered **twice**, providing a useful repeatability check:

| FCEUX frame | Token | Dict index | Pointer actual / expected | Primary next |
| ---: | --- | ---: | --- | --- |
| 6968 | EF | 32 | BF88 / BF88 | B861 |
| 7097 | ED | 30 | BF66 / BF66 | B864 |
| 7130 | EE | 31 | BF78 / BF78 | B866 |
| 7933 | EF | 32 | BF88 / BF88 | B861 |
| 7988 | ED | 30 | BF66 / BF66 | B864 |
| 8021 | EE | 31 | BF78 / BF78 | B866 |

**Status: v27's independent Bank6 English dictionary LOOKUP AND EXECUTION PATH PASS in real FCEUX.** This is stronger than static simulation: physical v27 cartridge identity, active-bank opcode validation, actual token-dispatch events, correct per-token pointer resolution, and repeatability are now evidenced by the user's trace.

## Boundaries of the result

- The trace **does not inspect pixels/PPU tile output**, so **rendered English glyph fidelity and line breaks remain unconfirmed**. Do not claim a visual PASS without the player's direct observation or capture.
- All six runtime hits correspond to **one reachable translated record, B6-356**, repeated twice. Full-script injection and full-English runtime coverage have not been attempted.
- Runtime output must not be inferred solely from 102 secondary-reader hits.
- The v27 accessible pilot still contains only 32 token entries (the previous 29 native entries plus ED/EE/EF). It is **not** yet a 144–160 phrase compression implementation.
- An inherited cosmetic tracer label reports D0-ED even though the new code counts D0-EF; interpret the actual token breakdown.

## Engineering direction after the pass

Preserve B6-356 as the *golden actual-emulator* token/pointer regression. Stop asking for new mapper/lookup tracer reruns. Inspect the actual English line layout once and use it to fix the control-code-aware encoder. Then implement source-locked **bulk** English dialogue insertion and phrase allocation against all 479 Bank6 records (plus 41 Bank8 events), track references/control codes, and perform only representative in-game QA. The model of 160 tokens co-located in Bank6 is still optimistic: 767-byte theoretical margin excludes controls and 6502 lookup machinery. Explicitly reserve decoder and pointer table bytes in the production allocator.

No commercial game ROM, full third-party translation dump or original source-derived rollback committed.
