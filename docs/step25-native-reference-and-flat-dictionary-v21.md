# Step 25 — Original 6502 text indirection and nonnested English phrase dictionary

**2026-10-24 · v21 read-only ROM engineering · 67 local tests PASS**

## What was actually established from the source ROM

The original Japanese NES game, exactly SHA-256
`ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`,
already implements a **single-level embedded text-reference mechanism** within Bank 6. This is not an assumption based on previous fan patches: we inspected the original fixed program bank's 6502 instructions and the Bank 6 indexed records.

Relevant fixed-bank CPU code:

| Routine | Observed function |
| --- | --- |
| `$EDC2` | Bank-6 text fetch wrapper; switches PRG bank using `$C3D4` |
| `$EDE7` | Recognizes source control `03` |
| `$EDFD` | Consumes the next byte as an index and calculates a two-byte pointer at Bank 6 CPU `$8002 + 2*index` |
| `$EE1C–$EE25` | Prepares secondary pointer and skips the referenced record's first two metadata bytes |
| `$EE2C–$EE4F` | Reads bytes from secondary reference until the special end/line condition; invokes the original character decoder |
| `$EE50` | Character-to-CHR-tile conversion, **not** itself a dictionary decoder |

The relevant state includes `$F5/$F6` (primary text pointer), `$F7/$F8` (secondary/reference pointer), and `$7980` (reference state). These relationships are inferred directly from instructions. Runtime call counts for a specific user playthrough have **not** been measured.

### Exact original-ROM corpus measurements

- **479** pointer-indexed Bank 6 records, total existing allocation **14,325 bytes**.
- **237** valid embedded `03 <index>` references in **172** different records.
- Exactly **29** unique referenced records, indices **1–29** in the first pointer group.
- The 29 referenced phrase bodies contain **no nested `03` references**.
- The source Japanese Bank 6 body has only **90 byte values not used as ordinary body bytes** once `03` index operands, the first two metadata bytes, and record terminators are excluded. **Some of those 90 are reserved control bytes**. Therefore **160 new token values cannot simply be presumed globally safe** in a mixed Japanese/English build.
- Zero-filled original ROM region `0x17B88–0x1800F` (Bank 5) is exactly **1,160 bytes**, independently SHA-gated and confirmed byte-for-byte zero.

**Important dependency:** the 29 shared referenced records are *not isolated*. Editing one may affect many other dialogue lines using its `03` reference. The v20 whole-bank packer preserves pointers and original metadata but does not yet audit the meaning of deliberate edits to these shared phrases; future automatic approvals must track these dependencies.

## Alternative compression test: flat phrase dictionary

Our prior nested pair-replacement simulation modeled symbols referencing previously generated tokens. The original game's reference path is **single-level**, so we ran another independent greedy model where **every new token expands directly to ordinary English characters, never to another token**.

Inputs: the same two public BlackPaladin2022 English script files, 479 verified reference positions including 478 usable drafts, 22,996 visible ASCII characters, and no copied prose in this repository. Candidate text was uppercased. Record boundaries were honored, but actual game linebreaking and other control codes were not modeled.

Each main record was charged **2 metadata bytes + 1 record terminator**. Dictionary layout below models a NUL-terminated byte sequence per phrase **plus a two-byte pointer per phrase**. These are storage estimates, not executable NES table definitions.

| Flat tokens | Estimated Bank 6 bytes | Bank 6 margin | Dictionary phrases + pointer bytes | Bank 5 zero-space margin |
| ---: | ---: | ---: | ---: | ---: |
| 96 | 14,276 | +49 | 409 + 192 = 601 | +559 |
| 112 | 13,753 | +572 | 473 + 224 = 697 | +463 |
| 128 | 13,294 | +1,031 | 532 + 256 = 788 | +372 |
| 144 | 12,884 | +1,441 | 599 + 288 = 887 | +273 |
| **160** | **12,512** | **+1,813** | **726 + 320 = 1,046** | **+114** |
| 176 | 12,161 | +2,164 | 791 + 352 = 1,143 | +17 |
| 190 | 11,882 | +2,443 | 855 + 380 = 1,235 | **-75** |

Under these assumptions, **144–160 flat tokens** look worth investigating before upgrading the mapper. The Bank 5 region is a plausible *static data* location for a 160-token dictionary. However, the original MMC1 switchable PRG window cannot expose Bank 5's table and Bank 6's dialogue concurrently without further changes.

## Why this is not a ROM patch yet

1. **Token namespace.** We have not identified 144–160 one-byte values that are conflict-free in the actual mixture of retained native references, still-Japanese text and control bytes. The native `03` index encoding already occupies two bytes per phrase reference and only has the 29 existing referenced targets.
2. **Runtime bank switching.** Dictionary bytes residing in original Bank 5 are not automatically accessible while the `$EDC2` reader selects Bank 6. An explicit safe switching strategy, RAM staging scheme, or other data placement must be proven.
3. **Decoder code placement.** A one-byte-token trampoline or dispatcher has not been built. Repeated `FF` runs in fixed Bank 15 are not proven free code caves; several appear in structured data.
4. **Capacity assumptions.** Estimates exclude actual linebreak commands, word-wrap, record-specific controls, dictionary runtime code, RAM usage, and any untranslated strings. A fully encoded Bank 6 may still need expansion.
5. **Original references.** We must maintain or explicitly rework all 237 native references and know when modifying the 29 shared targets changes other sentences.

A **read-only original-ROM audit** and a **lossless abstract flat-phrase simulation** are committed in `tools/native_dictionary_v21.py`, with regression tests in `tests/test_native_dictionary_v21.py`. The project’s local suite passed **67 tests**, of which 12 were added here. ROM-dependent tests skip when the original commercial game is absent.

## Next actionable engineering work

Map the complete `$EDC2–$EE4F` control-byte state machine and the fixed-bank text caller; establish a disjoint compression byte namespace and a bank-5-access strategy. Then create **one guarded, reversible single-token runtime smoke patch** on top of the FCEUX-accepted v1.7 build, validate it, and scale to automatic 144–160-token injection if it works.

No sequential playthrough is required to translate the script. Emulator use remains reserved for validating decoder behavior and a few representative translated locations.

**No original game ROM, copied third-party translation script, source-derived glyph rollback, or historical IPS binary is committed.**
