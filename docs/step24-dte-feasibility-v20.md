# v20 compression feasibility — test dictionary before mapper expansion

**2026-10-24. Read-only numerical simulation, NOT a working NES codec.**

The earlier engineering roadmap presumed we would need substantial additional PRG capacity because BlackPaladin's 478 available Bank 6 English drafts contain 22,996 visible characters, versus the 14,325-byte fixed original Bank 6 dialogue allocation. That remains true **without compression**.

We tested **greedy two-character dictionary substitution (DTE-style)** on the two public source files:

- `BlackPaladin2022/Dumped-Scripts/(NES) Square no Tom Sawyer MIX/tomsawyer_script_000.txt`
- `BlackPaladin2022/Dumped-Scripts/(NES) Square no Tom Sawyer MIX/tomsawyer_script_001.txt`

The known two `FFFF` separator entries `0x1820A` / `0x18252` were excluded. This leaves 479 legitimate indexed pointers, of which **478 have English candidates**. The 22,996 candidate characters contain **zero non-ASCII characters** in these two source files. We uppercased English and preserved record boundaries, but joined existing prose into single-line strings for a lower-bound capacity study. No external translation prose or dictionary entries were committed.

## Optimistic DTE capacity table

The model replaces each most frequent adjacent symbol pair with a new one-symbol dictionary token, iteratively. Tokens may themselves contain earlier dictionary tokens, so **nested expansion or an equivalent decoder implementation would be necessary**.

Each record is charged **two original Bank 6 metadata bytes plus one final terminator**, for a total of 1,437 record-structure bytes. The dictionary itself is assumed to be stored **outside Bank 6**, at two bytes per entry. This is not yet a verified storage location.

| Pair tokens | Compressed visible symbols | Estimated Bank 6 bytes (including headers/terminators) | Margin vs 14,325 bytes |
| ---: | ---: | ---: | ---: |
| 0 | 22,996 | 24,433 | **-10,108** |
| 64 | 14,767 | 16,204 | -1,879 |
| 96 | 13,549 | 14,986 | -661 |
| 112 | 13,057 | 14,494 | -169 |
| 128 | 12,621 | 14,058 | +267 |
| 144 | 12,234 | 13,671 | +654 |
| 160 | 11,882 | 13,319 | **+1,006** |
| 176 | 11,559 | 12,996 | **+1,329** |
| 190 | 11,303 | 12,740 | +1,585 |

The model is deliberately **optimistic**: it does not include the real game's explicit line breaks and other control codes, the untranslated record that lacks a draft, word-wrap constraints, text editorial changes, token-escape codes, extra RAM use, decoder machine code, stack depth for nested dictionaries, rendering timing, or storage for the 320–380 dictionary bytes. Nor does it prove that 160–190 distinct single-byte token codes are safely available without colliding with the original font/control grammar.

## Engineering implication

**Do not commit to an MMC1 mapper upgrade yet.** A correctly engineered one-byte DTE codec *might* allow the translated Bank 6 corpus to fit in the original 14,325 bytes, especially with 160–190 dictionary entries. But even a positive estimated margin is **not a functioning binary or completed translation**.

Next steps, in order:

1. Enumerate the actual Bank 6 bytecode/control-code grammar and locate all text-byte consumers in the fixed 6502 program bank (not just indexed pointer fetches).
2. Identify an exact, nonconflicting **token byte range**; compute decoder stack requirements if greedy dictionary tokens are nested.
3. Prove storage for the token table, decompressor, and scratch RAM. The zero-filled Bank 5 region has been observed, but its accessibility while Bank 6 is mapped must be established before claiming it is usable for dictionary lookups.
4. Generate a **single safe codec smoke test** with source-gated rollback and inspect in FCEUX. Preserve v1.7's already-accepted intro and four menu commands.
5. Recalculate space with line breaks, explicit controls, untranslated entries and actual chosen token IDs. If compression cannot fit, proceed with mapper-aware expanded storage research.

The independently reproducible estimator is `tools/dte_capacity_v20.py` with `tests/test_dte_capacity_v20.py`. It reads a private v1.8 TSV and writes aggregate statistics under ignored `work/`, **never a ROM**.

User gameplay is **not required for this capacity research stage**. No copyrighted game image, script dump, or historical IPS is redistributed.
