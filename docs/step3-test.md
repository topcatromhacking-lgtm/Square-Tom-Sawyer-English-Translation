# Step 3 — Partial glyph codec and reversible intro probe (2026-10-23)

**Static verification only; no emulator run.**

The public [BlackPaladin2022 Japanese script](https://github.com/BlackPaladin2022/Dumped-Scripts/tree/main/%28NES%29%20Square%20no%20Tom%20Sawyer%20MIX) independently identifies the exact ROM pointer locations that our extractor reads. Matching 29 initial dictionary/name records character-by-character against the clean ROM produced **88 distinct, conflict-free glyph encodings**. The table is in [glyph-map-v01.tbl](glyph-map-v01.tbl). We do not commit the Japanese dialogue, edited ROM, or the private decoder output.

From 479 indexed records, 10,306 of 12,717 bytes other than 00/01 have a confirmed glyph mapping (81.04%). The decoder leaves unknown glyphs as <XX>; the roles of 00/01 and other control codes need runtime verification. A complete translation codec has NOT been established.

**Important correction:** The previous bank-8 tiled-art inspection overlapped the intro pointer table at file offset 0x2124D and its encoded script beginning at 0x2129F. We have NOT identified the dialogue font in PRG ROM, and apparent letters in the naive tile atlas are NOT adequate proof of a font. Treat that earlier font claim as superseded.

## Reversible intro diagnostic

The opening narration's first pointer at file offset 0x2124D is $928F, corresponding to file offset 0x2129F in zero-based 16 KiB PRG bank 8. We change only eleven glyph bytes at 0x212A0–0x212AA to:

\`70 6A 71 8F 8F 8F 8F 8F 8F 8F 8F\`

This is **テスト** (katakana TEST), followed by spaces. The original preceding space, following line separator 01, all pointers, record lengths, and iNES header are unchanged.

Build the forward and reverse IPS diffs locally, against the clean Japanese ROM:

\`\`\`sh
python -m unittest discover -s tests -v
python tools/decode_indexed_text.py "/private/Square no Tom Sawyer (Japan).zip" --out work/private-decoded.json
python tools/make_intro_probe.py "/private/Square no Tom Sawyer (Japan).zip" --out work/intro-probe
\`\`\`

Offline validation: **24 source-free unit tests pass**. Forward patch applies and reverse patch restores the exact original SHA-256. Patched ROM SHA-256: \`89d45d1b7e7aeb53ae8540c0d5be7ce961998e9be4a859252d4b2dd6e5fcef0b\`. Original SHA-256: \`ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb\`.

**Required next proof:** Apply the forward IPS to a *copy* of the clean ROM, cold boot in Mesen/MesenCE (not a savestate), start a new game, and inspect the first narrator line. It should show テスト; obtain a screenshot or report no change/crash. We have not verified that visual outcome. Do not save over existing saves.

This test is NOT yet an English translation, and it does not solve MMC1 ROM expansion. The ongoing BlackPaladin script translation is already available; do not duplicate that effort. Our engineering priority is controllable insertion, bank layout, and QA.
