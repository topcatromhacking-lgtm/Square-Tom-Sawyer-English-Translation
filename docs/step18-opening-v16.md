# v1.6 — English opening with actual event-pointer relocation (2026-10-24)

**Offline build PASS; FCEUX visual test pending.** This is an English opening-cutscene prototype, NOT the completed first quest.

## Implementation

- 12 consecutive event text records in PRG bank 8 translated (narration, river/ticket dialogue, Tom waking up). New English text is concise and authored for this test.
- Every line <=20 visible characters, with 3 opening narration lines and <=2 dialogue lines.
- Original record window: 0x2129F through 0x213EB, capacity 333 bytes. New encoded text: 324 bytes, leaving nine padding bytes.
- Ten event pointer words at file 0x2124D..0x21263 are updated. The pointer at 0x21265 and all subsequent original ROM bytes are preserved.
- Project-authored glyphs replace 26 Japanese font slots with Latin A–Z plus six punctuation symbols. The original text renderer/font loader is not modified.
- Canonical A–Z code range 0x6E..0x87, numerals 0x10..0x19. Correction from Translation 2.0: apostrophe is 0x88; question mark is 0x8D. v1.5 previously reversed these two and has been fixed.

## Offline verification

- Source SHA-256: ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb
- Patched SHA-256: 9709c1df01b9fb304ee9dd39f5dd48afe43aaf346827b83f9ab353dd18cae4ba
- Forward IPS: 832 bytes, SHA-256 b96f5b34816439d24437ea816f66004c878bb75b0ee55c7b63c48624fba2f06e
- Byte-exact reverse IPS regenerated locally restores the exact original ROM.
- Two independently implemented builders generated identical forward IPS data. 11 source-free v1.6 tests and exact original-ROM integration checks passed.
- Modified full-ROM size remains 262160 bytes, header and mapper unchanged.

## FCEUX user test

1. Use exact CLEAN Japanese NES ROM, with prior experimental and legacy .nes.ips softpatches removed.
2. Place the v1.6 English Opening IPS as Square no Tom Sawyer (Japan).nes.ips beside the clean ROM; cold boot New Game.
3. Capture the opening UNITED STATES / MISSOURI / 1855, ONE NIGHT, subsequent WHERE AM I? / WHAT'S THAT TOWN?, TOM, IT'S SOUTHWEST., and Tom's final WAKE UP! dialogue.
4. Report visual font issues, apostrophe/question mark corruption, skipped dialogue, freezes or pointer issues. Do not save: later Japanese content still renders incorrectly through the English font.

## Follow-up

After FCEUX confirms the sequence, expand the English scope into remaining opening events, and bank-6 NPC, menu and battle text. The original 333-byte window is only an in-bank relocation experiment and does not resolve full-game capacity or expansion.

No ROMs, predecessor IPS binaries, original Japanese glyph rollback data or copied third-party script dumps are committed.