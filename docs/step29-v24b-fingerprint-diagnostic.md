# Step 29 — v24b fixes a one-shot FCEUX fingerprint false negative

**October 25, 2026 — user trace received.** The original `SquareTomSawyer_v24_token_trace.txt` records 9,390 frames, `Experimental v23 ROM fingerprint: false`, `Expected v23 at $EDE7, got $00`, and zeros for Bank 6 dispatch, tokens, resolver and secondary reader. The earlier v24 script checked `memory.readbyte($EDE7)` **once at startup** and used the resulting `valid=false` state to suppress all counters, permanently. **No Bank 6 execution conclusion can be drawn from those zero counters.**

Independently reapplying the published v23 IPS to the SHA-256-gated original game yields exact fixed-bank decoder bytes `C9 D0 90 06` at ROM file offset `0x3EDF7` and `38 E9 CF 85 F1 A9 00 85 F2` at `0x3EE0D`. The patched ROM SHA-256 is `27a3cd09f75714458929aaca3bee3c4777cdba9b1ee4cd89ebb2ab24f2c2394b`. Therefore the delivered **v23 IPS data is correct**. We have *not* yet determined whether the user's FCEUX session applied it, nor whether the initial zero was a transient mapper state.

## Correction

`tools/fceux_v24b_token_trace.lua` reads each decoder signature from **two independent views**:

1. `rom.readbyte(file_offset)` using iNES-header-inclusive physical ROM offsets, `0x3EDF7` and `0x3EE0D`.
2. `memory.readbyte(cpu_address)` using mapped CPU addresses `$EDE7` and `$EDFD`.

It recognizes v23, original/unpatched, all-zero/unmapped and unavailable/other results independently. It retries every **60 frames**; it does not confuse an early CPU `$00` with proof that the ROM is wrong. If either view matches v23, the observer can count real dispatch/resolver/secondary execute callbacks. Report filenames change to `SquareTomSawyer_v24b_token_trace.txt` and include both signatures, check count, and execution counters.

FCEUX's documentation says `rom.readbyte` reads the actual ROM including the header and `memory.registerexec` uses CPU address space, which can be bank-switched. See https://fceux.com/web/help/LuaFunctionsList.html.

## Tests, scope and next steps

Four local tests PASS: (a) v23 cartridge with CPU memory initially zero and later mapped, (b) unpatched cartridge, (c) cartridge API unavailable with delayed CPU mapping, and (d) no RAM/ROM/controller mutation. The new diagnostic adds **no IPS** or game translation. The previous v23 FCEUX evidence remains **boot + English opening only**. Bank 6 `D0–EC` token execution and rendered text are not yet confirmed.

User steps: stop v24 Lua; retain same original ROM plus v23 patch; start v24b Lua **from current game position**; let it run briefly and optionally trigger one nearby LOOK/NPC response; return `SquareTomSawyer_v24b_token_trace.txt`. A zero token count on a line without references remains inconclusive, even with verified decoder bytes.

Do not claim v23 runtime token PASS before genuine Bank 6 token + resolver/secondary execution evidence is obtained.
