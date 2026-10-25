# Step 31 — v25 same-Bank6 phrase dictionary capacity hypothesis

**October 25, 2026.** Following the user-confirmed v24b live Bank6 one-byte-token trace, we reexamined the proposed storage layout.

## New engineering option

The v21 flat English phrase-compression model assumed a separate dictionary in Bank 5 and raised a simultaneous Bank5/Bank6 visibility problem. But the compression model leaves **unused room inside the original Bank6 14,325-byte dialogue allocation itself**.

An allocation layout could place, contiguously *inside* Bank6:

1. 479 compressed translated records, each with a two-byte metadata prefix and one `00` terminator.
2. A separate two-byte-per-token dictionary **pointer table**.
3. NUL-terminated shared English phrase bodies.
4. Remaining padding.

This would **not require bank switching for dictionary reads**, provided a patched interpreter can select the new pointer-table base without disturbing the game's existing 479-record primary text pointer table. That separate table lookup has **not** been implemented; v23 presently computes token targets through the original first pointer group.

## Optimistic Bank6 joint-storage budget

The figures below reuse the earlier nonnested ASCII phrase model (which did not preserve genuine FCEUX linebreak/control streams). It charges all 479 record prefixes and terminators and the phrase dictionary + its own table. It does not include any required new interpreter routine code, or cost to move/replace original shared targets.

| Tokens | Compressed record bytes | Dictionary pointer bytes | NUL-terminated phrase bytes | Combined Bank6 occupancy | Margin within 14,325 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 144 | 12,884 | 288 | 599 | 13,771 | **554** |
| 160 | 12,512 | 320 | 726 | 13,558 | **767** |
| 176 | 12,161 | 352 | 791 | 13,304 | **1,021** |

This is useful because it removes the presumed need for a Bank5 dictionary *in the space model*. The addressable Bank6 window remains 16KiB. **It is not proof of usable decoder code space, a valid 160-token one-byte encoding, or a playable translated image.**

For 160 tokens the theoretical unused capacity is **767 bytes**. Just **768 additional encoded linebreak/control/glyph symbols** would make that configuration overflow. The numbers must therefore be recomputed from faithful **per-record game grammar** rather than flattened prose.

## Critical unresolved runtime work

- The v23 decoder directly maps `D0–EC` to **29 current first-group shared records**. A new pointer table elsewhere in Bank6 needs a distinct lookup or retargeted table base. Simply overwriting 160 of the 479 existing primary pointers would destroy legitimate NPC strings.
- A 160-entry dictionary cannot reuse the 29-code `D0–EC` namespace alone; the token-byte namespace must coexist with the actual English font codes and controls. It must not classify normal English letters as tokens.
- A source-verified 6502 table-lookup change, bank-aware RAM/state handling and runtime validation are still required. The 13-byte v23 interpreter edit is not magically sufficient.
- Long translated lines, controls, mixed Japanese fallback entries and original native shared-reference dependencies must be modeled.
- Address and capacity guards are necessary but do not prove semantic rendering.

## Source-only layout planner

`tools/same_bank_dictionary_layout_v25.py` exposes exact original Bank6 file/CPU mapping and fails closed if the proposed record/table/phrase layout exceeds `0x18812..0x1C006`. The companion regression tests cover 144/160/176-token budgets, strict overflow, source record count, and mapped CPU bounds.

**Next engineering task:** identify a safe method for the native reader to address an independent dictionary pointer base, without reassigning the original 479 dialogue pointers, then create **one actual compressed English sentence** and measure its visual result in FCEUX. Only after that scale to the complete translation database.

The live v24b result is accepted independently in [step 30](step30-v24b-live-token-execution.md). **No additional user startup diagnostics are needed.**
