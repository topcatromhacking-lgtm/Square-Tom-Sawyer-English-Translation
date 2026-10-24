# v1.5 — One-byte English encoding and bounded dialogue relocation

**2026-10-24 | Source-only milestone; not yet a playable translation.**

## The encoding decision

The supplied historical `Square NTS Translation 2.0.ips` explicitly repaints original glyph input codes `6E–87` as uppercase A–Z. We adopt these as the *canonical English A–Z byte positions*. The clean original narration's year 1855 uses `11 18 15 15`; original digit codes are therefore `10–19`. The verified source uses space `8F`, explicit line separator `01`, and text terminator `00`.

`tools/english_codec_v15.py` implements strict encoding/decoding with uppercasing, no implicit word-wrap, and clear unsupported-glyph/line-width failures. **Historical correction (v1.6):** Translation 2.0's bitmap shapes and dialogue confirm apostrophe=`88` and question mark=`8D`; the original v1.5 values were reversed. Additional punctuation codes are `-`=`89`, `,`=`8A`, `.`=`8B`, `!`=`8C`; they use project-authored glyphs in v1.6. Colon is now deliberately unsupported rather than guessing `23`. Full FCEUX visual validation of punctuation remains pending.

## Bounded relocation

`tools/relocate_dialogue_v15.py` repacks **whole encoded record bytes** rather than changing portions of unknown record metadata. It operates on the SHA-256-verified original Japanese ROM, takes a contiguous range of the 479 verified indexed records within ONE pointer group in PRG bank 6, and requires the new aggregate data to fit the **same total address range**. It updates each affected little-endian pointer, preserves untouched records verbatim, maintains terminating zero bytes, pads unused bytes with zero, and rejects any unexpected change outside the data/pointer window.

The code **does not** implement cross-bank relocation, ROM expansion, or detect hidden hardcoded references outside the pointer table. It is a structural prerequisite, not yet a fully runtime-validated engine mod.

### Offline original-ROM integration proof

On the verified Japanese ROM, a disposable integration experiment repacked record indices 1–3, expanding one by one byte and shortening its neighbor by one while preserving the `00 00` initial metadata and `00` terminators. One indexed pointer relocated from CPU `$8814` to `$8815`; the size and all unselected areas remained unchanged. This test ROM is intentionally **not** shipped or committed, because the altered records are dummy data and untested in FCEUX.

### Tests

- **17 new source-free regression tests passed locally**, covering original alphabet/numeral codes, multi-line encode/decode, punctuation round-trip, strict encoding rejection, record-window repack, pointer changes, unchanged original regions, group crossing and overflow refusal, and checksum guards.
- The project previously passed 46 earlier tests, giving **63 local regression tests** when combined with v1.4 (same environment).
- CI will run the source-free regression suite; actual FCEUX gameplay behavior is **not** yet verified.

## Next steps

1. Verify punctuation font graphics and text-window widths in actual FCEUX.
2. Classify embedded record metadata and prefix/dictionary grammar, especially initial `00 00` bytes in bank 6.
3. Build a genuine English first-quest segment using externally referenced candidate translations, not fake dictionary edits.
4. Test real runtime record pointer relocation before relying on it for NPC dialogue.
5. Address the larger approximately 10 KiB aggregate positive overflow through safe allocation or mapper-aware ROM banking changes after analyzing the affected control flow.

**Never distribute original ROMs, third-party IPS binaries, copied translation dumps, or extracted game-data rollback glyphs from this public repository.**
