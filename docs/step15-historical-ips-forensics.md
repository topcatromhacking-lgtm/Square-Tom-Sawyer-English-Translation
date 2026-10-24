# Step 15 — Forensics of the actual historical English IPS patches (2026-10-24)

**Status:** confirmed with user-uploaded original Japanese ROM plus both predecessor IPS ZIP archives. This replaces the earlier source-only speculation. Do not invent more font-loader patches.

## Input artifacts, metadata

- `tomsawee.zip` → `TOMSAWEE.IPS` (3,921 bytes; 83 IPS records).
- `t-snts2.zip` → `Square NTS Translation 2.0.ips` (2,979 bytes; 73 IPS records).
- Exact original ROM: 262,160 bytes; SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`; CRC32 `AEA5B066`.

Each IPS parsed and applied to the exact original **independently**, never stacked. Resulting ROMs were analyzed in memory and not committed or distributed.

| Property | TOMSAWEE | Translation 2.0 |
| --- | --- | --- |
| Bytes actually modified | **3,123** | **2,333** |
| Patched ROM size | 262,160 | 262,160 |
| Patched SHA-256 | `f249cf778ac69e0d8a54b2bee41d67b72dfac138df73f7fbd2bb54fc5744d84b` | `5593dde0f8577fd4679884959008891638092ddcafbec9f130a02e97a7951c82` |
| Original font changed bytes | **214** | **220** |
| 479 indexed dialogue records touched | **110** | **73** |
| Changed pointer-table bytes ($18010–$18411) | **0** | **0** |
| Changed bytes in known CPU $EE50 decoder | **0** | **0** |
| Changed bytes in known CPU $C587 font loader | **0** | **0** |
| Changes to original blank font area $17B88–$1800F | **0** | **0** |
| Original record-ending nulls overwritten | **23** | **14** |

## Most useful discovery: complete Latin font without custom loader

The predecessors **repaint original Japanese glyph graphics** as Latin A–Z and encode English sentences by reusing those original character slots. The original CPU font loader and Japanese glyph-to-tile converter remain unchanged.

- `TOMSAWEE.IPS`: uppercase A–Z use input codes `$5E–$77` (A=$5E, Z=$77), with character bitmaps at `0x17A00–0x17ACF`.
- `Square NTS Translation 2.0.ips`: uppercase A–Z use `$6E–$87` (A=$6E, Z=$87), largely updated at ROM `0x17A81–0x17B7E` (plus a few font corrections elsewhere).

Our v1.1 patch demonstrated that this original-font repurposing technique works in FCEUX: AMERICA / MISSOURI / ONE NIGHT, 1855 rendered correctly. The later untranslated Japanese dialogue looked corrupted because the original kana font slots had been replaced; historical partial patches inherently have that same design limitation. **A permanent bilingual font switch is unnecessary for a final all-English release.** It remains a possible debugging convenience for incomplete builds, not the principal project goal.

## Same original ROM, different encodings and translations

Both IPS files keep the same original pointer list and file length; each reflows internal linebreak bytes inside the existing 39-byte first narration record. Decoding the observed bitmap order:

- TOMSAWEE: `AMERICA` / `MISSOURI STATE` / `YEAR 1855` followed by punctuation
- Translation 2.0: `UNITED STATES` / `MISSOURI` / `YEAR 1855` followed by punctuation

The literal first two linebreak positions also differ. They are a useful precedent for shortening and reflowing English text **within a fixed allocation**.

Across the patches, **1,711 file offsets were changed by both**, but only **59** share the same final byte. The resulting patched ROMs differ in **3,686** byte positions. Thus these are not mergeable as simple patch layers. Neither patch's A–Z alphabet encoding is directly compatible with the other.

## Changed bytes per 16 KiB PRG bank

| Bank | TOMSAWEE | Translation 2.0 |
| --- | ---: | ---: |
| 5 (font + other data) | 237 | 242 |
| 6 (indexed dialogue) | 2,074 | 1,370 |
| 8 (intro and event dialogue) | 482 | 315 |
| 10 (other interface/data) | 172 | 225 |
| 13 | 126 | 126 |
| 14 | 0 | 20 |
| 15 (UI and fixed-bank data) | 32 | 35 |

No other bank was modified in either patch. Edited fixed-bank bytes are found in additional text/data regions, not the known $EE50/$C587 routines. The rest of the bank-level executable code was **not** fully disassembled, so do not generalize to 'no code changes anywhere.'

## Risks and unsettled questions

Both patches overwrite some original record-final null bytes while leaving the pointer table unchanged. These may be intentional reuse or packing conventions in some name/dictionary entries; a runtime test is needed to establish whether they are safe. Modified-record counts are **not full-game translated percentages**. The two supplied ZIPs contain no bundled author/readme metadata, so TOMSAWEE→Kikuyama v0.07 and Translation 2.0→Dushbadge v2.0 are plausible but not independently proven by archive provenance.

The original dialogue bank's available text capacity is still the major problem for full translation; BlackPaladin's August 2026 ROM-expansion discussion makes the same observation. The historical patches fit only selected parts in-place, retaining all original pointers.

## New project plan

1. **Freeze v1.4 speculative font-loader edits.** Retain v1.1 as the known-good graphical baseline.
2. Choose **one** Latin code map; likely adopt the more recently supplied Translation 2.0 font ($6E–$87) after visual review, or generate our own coherent standard mapping. The main requirement is one encoder for every scene.
3. Use the two historical patches as reference translations; use BlackPaladin's bilingual pointer-indexed script as the comprehensive translation basis, with attribution and editorial checks.
4. Create a length/allocation table covering all 479 main records, their English candidates, controls and line breaks. Flag overflow, dictionary prefix interactions, pointer assumptions and modified original terminators.
5. Develop safe **dialogue bank relocation and possibly PRG expansion** for the complete translated script; do not silently overwrite subsequent strings.
6. Assemble an all-English playable first-quest build and test both text windows and menus. The original Japanese ROM and separate source IPS archives remain untouched.

Full reproducible report and source-only program: `Square_no_Tom_Sawyer_Historical_IPS_Forensic_Audit_20261024.zip` supplied in the conversation; the ZIP contains a SHA-gated original-ROM analyzer, 8 passing tests, JSON metadata, and TSV files with the alphabet and per-bank edits. It contains **no original ROM or historical IPS binaries**.

External translation context: BlackPaladin's public scripts at https://github.com/BlackPaladin2022/Dumped-Scripts and August 2026 text-capacity thread at https://community.romhackplaza.org/threads/technical-nes-square-no-tom-sawyer-nes-rom-expansion.4856/ .
