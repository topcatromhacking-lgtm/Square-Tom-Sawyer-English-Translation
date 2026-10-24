# v1.0 font capacity result and v1.1 English opening (2026-10-24)

**v1.0 user-uploaded FCEUX log: PASS.** The actual intro began at frame 546; the CHR-RAM and nametable scan was captured at frame 581. The report contains exactly 512 tile rows, 256 in each of the two pattern banks, with identical occupancy and graphics measurements in both banks. Both have **253 populated tiles** and **3 entirely blank tiles**: `21`, `8A`, `FF`. Only `21` and `8A` are not currently referenced by the sampled nametables. The blank `FF` tile is referenced 3,770 times, reflecting the background's blank filler. The survey reads all four logical nametable pages (including mirrored copies), so counts cannot be interpreted as unique on-screen tile cells. A blank or unreferenced tile *in the intro* may be used by other game screens.

**Conclusion:** We cannot hold a permanent 26-letter Latin alphabet solely in existing empty CHR-RAM tiles. The game needs a dedicated English font storage/routing arrangement or runtime font swapping. The v0.5 first-line HELLO remained the confirmed proof of the original 1-bit Latin bitmap technique.

## v1.1 offline diagnostic: complete uppercase font and first three English lines

A guarded generator is committed as `tools/make_english_intro_v11.py`; 8 source-free regression tests passed in the accompanying package. It creates a 40-record forward IPS and an exact reverse IPS, and pins both original and patched ROM SHA-256 checks. The original clean ROM and game graphics are excluded from Git.

The patch defines 26 uppercase letters, ten numerals and a comma as 37 custom 8-byte fonts in original Japanese font positions and rewrites the first three introduction lines within their exact existing byte capacities (12, 9, 15 characters) to:

- `AMERICA`
- `MISSOURI`
- `ONE NIGHT, 1855`

All the dialogue pointers, original line separators (`01`), opening text terminator (`00`), PRG-ROM length, and header stay unchanged. The original Japanese glyph patterns replaced by the experiment are restored byte-for-byte by the reverse IPS.

**Warning: Intro-only test, not bilingual support.** Because 37 existing Japanese font entries are temporarily repainted, other Japanese dialogue will render incorrectly if the softpatch stays loaded. Do not save or play through with the patch. Remove the softpatch after screenshot. v1.1 has passed ROM identity/rollback verification offline but is **not yet verified in FCEUX**.

Source original SHA-256: `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`. v1.1 patched SHA-256: `a76bb5678a183ba2b36e4fb27ac90b4597c08e850be91db9260dd050e0fa940e`.

**User test:** take the forward `Square_Tom_Sawyer_English_Intro_v11.ips` from the accompanying ZIP, rename it `Square no Tom Sawyer (Japan).nes.ips` beside the original clean `.nes` (no previous IPS), open New Game in FCEUX, and send one screenshot showing the three opening lines. If they render, proceed to a runtime English-specific font-load and Japanese restoration hook, rather than expanding more destructive tests.

The ZIP contains a self-contained source script, tests, executable IPS and rollback, the manifest, and the summarized v1.0 CHR survey. `patches/*.ips.hex` in GitHub stores the reversible patch data as portable ASCII hex text.
