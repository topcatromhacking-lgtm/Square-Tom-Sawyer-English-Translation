# Step 33 — v26 report: execute-hook hit, but mapped Bank 6 helper not yet proven

**2026-10-25 — user FCEUX trace analyzed.**

The user's `SquareTomSawyer_v26_dictionary_trace.txt` reports:

| Trace field | Actual |
| --- | --- |
| ROM file signature | **v26** |
| Mapped CPU signature at periodic check | **wrong Bank6 helper ($BF0A=$09)** |
| Frames | **7,238** |
| Bank 6 text dispatches | **84** |
| Single-byte tokens D0–ED | **1**, value **DD** |
| Execute hooks at BF0A | **1**, frame **6193** |
| Secondary reader EE2C executions | **12** |
| New English ED token executions | **0** |
| Old tracer status | INDEPENDENT DICTIONARY LOOKUP EXECUTED |

**Key correction to interpretation:** the reported `$BF0A=$09` is a real byte at **PRG Bank 14** offset `0x3BF1A` in the exact source/patch. The new helper in **PRG Bank 6** at `0x1BF1A` starts with `$8C`. This strongly suggests the CPU window had already switched to another PRG bank when v26 periodically checked CPU memory, rather than indicating a corrupt v26 IPS.

However, `memory.registerexec($BF0A)` hooks the **CPU address**, not necessarily a specific physical PRG bank. The v26 tracer accepted **any** execution at that address after confirming the ROM file fingerprint, regardless of which bank was mapped **at the moment of execution**. We therefore have confirmed ROM identity, one `DD` token and a nearby BF0A hook, but **not yet proof that the new Bank 6 helper instructions ran correctly**. The old status line was overconfident.

## v26b live bank witness — no new IPS

`tools/fceux_v26b_live_bank_witness.lua` runs on the **same v26 ROM** and keeps the observation strictly read-only. It records:

1. The correct physical v26 cartridge signature and the ordinary/idle CPU byte at `$BF0A` independently.
2. At every actual BF0A instruction-hook callback, whether **all 26 mapped CPU bytes** match the Bank 6 helper.
3. The pending dictionary index (`$F1`) and, on entry to `$EE1C`, whether the resolved `$F7/$F8` pointer matches the corresponding word in the **physical v26 dictionary table** at file offset `0x1BF34 + 2 * index`.
4. The primary dialogue text stream pointer (`$F5/$F6`) on token dispatch, logged as `primary_next`. This can identify a reachable, nearby record for the next **real English phrase-display** pilot, without requiring a sequential playthrough.

**Local verification:** source-ROM SHA-gated reconstruction produced the exact v26 patched ROM. In a Lua/FCEUX mock using this actual patched ROM, Bank 14 at idle + Bank 6 at BF0A execution produced **one verified helper and one matching pointer**; forcing Bank 14 at BF0A execution produced **a foreign-bank hit and a pointer mismatch**. The observer also passed a no-write API check. This is local simulation, **not yet actual FCEUX acceptance**.

## Short user test

1. Keep the current cumulative **v26** ROM. **No new IPS or game restart is needed.**
2. Stop the earlier v26 Lua script and load `fceux_v26b_live_bank_witness.lua`.
3. Trigger one reachable LOOK or nearby NPC response and return `SquareTomSawyer_v26b_live_bank_trace.txt`.

**Acceptance gate:** `BF0A confirmed Bank6 helper bytes at hook time > 0` *and* `Dictionary pointer compared MATCH at EE1C > 0`. Only then call the independent Bank 6 dictionary's actual lookup **runtime PASS**. The $ED → HELLO visual test and larger English dictionary remain subsequent work.

No commercial ROM, altered ROM, source-derived rollback or third-party script text is committed to GitHub.
