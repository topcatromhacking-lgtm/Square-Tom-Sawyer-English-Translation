# v1.0 — Latin font capacity audit (2026-10-24)

## Verified v0.9 milestone

The user-provided FCEUX runtime log captures frame 546 as the actual first narration, with 78 ignored startup reads, 39 text reads, **36 decoder entries, 36 matching outputs, 0 unmatched**. An independent comparison of all 36 observed input->tile mappings with the reconstructed 6502 $EE50 algorithm gives **36/36 correct**. The two $01 bytes represent line changes; a terminal $00 is not rendered as a glyph.

## Original ROM static audit

From the original SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`, precisely 479 candidate indexed records total 14,325 bytes. Among the ordinary direct-glyph codes $09-$8E, **only five** do not appear in those records: `5C, 78, 82, 8A, 8E`. The 8-byte 1bpp font rows at `0x17710 + code*8` are zero for `02, 1A, 8E, 8F`. Thus **only 8E is both blank and absent** from the indexed dialogue; FCEUX confirms input 8E maps to solid tile FE. None of this proves other code absence outside the indexed bank.

Conclusion: creating an entire 26-letter Latin alphabet simply by using spare original input codes is not feasible. The v0.5 HELLO still works but uses replaced Japanese font glyphs. The v0.6 high-byte slot experiment failed because most high input codes encode Japanese composites.

## Proposed solution and v1.0 test

Future engineering should introduce a separate Latin mapping/bitmap area, or an English-specific rendering mode, through an explicit decoder hook. Before allocating CHR-RAM tiles, we need a grounded occupancy map rather than claiming lower tile IDs are free.

`tools/SquareTomSawyer_v10_Font_Capacity_Trace.lua` samples each of 256 tiles in the two pattern banks and four nametable views **35 frames after the real intro begins**, collecting only occupancy metadata (not raw game graphic bytes). It triggers solely on CPU read address $928F with FCEUX callback PC=$8393, ignoring startup copying.

`tools/analyze_font_capacity_v10.py` independently checks v0.9 input/output sequences, original-ROM unused-code counts, and optionally v1.0 tile survey. Five unit tests passed locally. Original ROM/graphics/text are never committed. **The v1.0 Lua itself has not yet been run in FCEUX.**

## User test

FCEUX with original Japanese .nes (no IPS), Lua script loaded before New Game, let the intro appear. Send back `SquareTomSawyer_font_capacity_v10.txt` from the Lua directory. If no `REAL_INTRO_START` or `TILE` entries appear, send the report anyway so we can correct the diagnostic.

**Caveat:** tile emptiness is scene-specific; future levels, sprites and UI may use tiles that look available during this introduction.
