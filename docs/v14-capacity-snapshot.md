# v1.4 preliminary English capacity snapshot — 2026-10-24

## Public reference analyzed

[BlackPaladin2022 / Dumped-Scripts](https://github.com/BlackPaladin2022/Dumped-Scripts), files `(NES) Square no Tom Sawyer MIX/tomsawyer_script_000.txt` and `tomsawyer_script_001.txt`, fetched through the connected GitHub source. This analysis contains **aggregate numbers and original pointer metadata only**; none of the bilingual script passages is committed.

## Reference reconciliation

- Script file 000: **411** pointer headers.
- Script file 001: **70** pointer headers.
- Total raw headers: **481**.
- In the exact Japanese source ROM, file offsets `0x1820A` and `0x18252` contain `FFFF` pointer group delimiters, not dialogue pointers. BlackPaladin lists both with ambiguous external text address `0x2000F`.
- Excluding those two gives **479 distinct, valid pointer-field positions**, with group counts `251, 35, 123, 70`, matching the independently verified ROM parser.
- Source string offsets are monotonically increasing after excluding separators; the first starts at `0x18812` and the last at `0x1BFFE`. The final original text end is `0x1C007`.
- The consecutive external string offsets imply **14,325 allocated text bytes**, independently matching the ROM inventory. This confirms the *offset sequence at the aggregate level*. The v1.4 local importer still compares every individual pointer/string-offset pair against the ROM before treating it as an exact match.

## Preliminary candidate lengths

The reference text following each record's `[ED]` marker was joined into a single candidate string; hand-authored uncertainty markers starting `^((` were excluded. Under the **simplifying lower bound** of one byte per visible character plus one byte per string terminator:

| Metric | Value |
| --- | ---: |
| Valid main-bank indexed records | **479** |
| Records with an English candidate | **478** |
| Records without a usable English candidate | **1** |
| Total candidate visible characters | **22,996** |
| Minimum candidate bytes, including 478 terminators | **23,474** |
| Original total allocated bytes | **14,325** |
| Candidates exceeding their allocated record lengths | **374** |
| Sum of **positive, per-record minimum overflow** | **10,070 bytes** |
| Net candidate requirement over total allocation | **9,149 bytes** |

These are **not final encoded output sizes**. Exact sizes require a verified Latin character/punctuation table, control code inventory, linebreak and word wrapping policies, optional dictionary/compression, and editorial rewriting. Individual English candidates may be refined or shortened. Since the input is an external translated script, records need manual editing and attribution review. No modified game image was built from this estimate.

## Engineering implication

It is unsafe to pack the current candidates directly into existing fixed-length record allocations. A 479-record master manifest, precise encoding and guarded relocation should precede any large English text insertion. In-bank relocation may suffice for a few records, but 10 KB positive overflow strongly suggests controlled script-bank space allocation and possibly mapper-aware ROM expansion.

The executable v1.4 tool is `tools/build_master_inventory_v14.py`; its output containing translated script text belongs in ignored local `work/v14/`, not Git.
