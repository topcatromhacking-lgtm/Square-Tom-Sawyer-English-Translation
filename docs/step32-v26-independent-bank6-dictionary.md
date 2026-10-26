# Step 32 — v26 independent Bank 6 dictionary pilot

**October 25, 2026 — original-ROM build PASS, FCEUX new-lookup execution pending.**

## Why this changes the architecture

The user-confirmed v24b trace showed the v23 one-byte token dispatcher executing `D1` and `DD` inside real FCEUX. However, the 29 v23 tokens were resolved through the game's **original dialogue pointer table**. Allocating 160 additional English phrases there would overwrite real NPC records.

**v26 creates an independent dictionary pointer table inside Bank 6**, without modifying any of the game's 479 dialogue pointer values or its original 29 shared phrase bodies.

## Exact native 6502 change

The original text reader at CPU `$EDC2` selects PRG Bank 6. The native reference resolver at `$EE0A` calls the shared index-pointer helper `JSR $ED9D`. v26 redirects **that call only** to `JSR $BF0A`. The shared original helper at `$ED9D` remains untouched, protecting its other callers.

The new helper is an exact 25-instruction-byte clone of `$ED9D`, except that the two immediate pointer-table base values change from `$8002` to `$BF24`. A one-byte NOP aligns the following pointer table. Because the original reader has already selected Bank 6, this is a plausible same-bank execution path—but **new helper execution has not yet been confirmed in FCEUX**.

| CPU address / ROM offset | Size | New content |
| --- | ---: | --- |
| `$BF0A` / `0x1BF1A` | 26 | cloned helper with independent base + NOP |
| `$BF24` / `0x1BF34` | 62 | sentinel plus 30 little-endian phrase pointers |
| `$BF62` / `0x1BF72` | 8 | separate `00 00` metadata + English `HELLO` + terminator |
| `$BF6A–$BFF6` | **141** | remaining zero-filled unused indexed-text capacity |

The dedicated phrase table's entries **1–29** target exactly the previously used 29 source records. Entry **30** points to a completely separate new English string, selected by token `$ED`. The original main indexed dialogue pointers are identical to v23.

### Explicit diagnostic limitation

For proof of encoding, **B6-420** is temporarily changed from its four-byte original Japanese literal to one `$ED` token with three padding zeros. Its original seven-byte allocation is unchanged. When reached, this will display `HELLO` **rather than the correct story dialogue**. It is *not* a reviewed translation. No long playthrough is expected to reach B6-420. Previously observed ordinary `D1` and `DD` references are enough to test the relocated helper's execution.

## Offline validation

Original ROM SHA-256:

`ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`

v23 baseline patched SHA-256:

`27a3cd09f75714458929aaca3bee3c4777cdba9b1ee4cd89ebb2ab24f2c2394b`

v26 experimental output ROM SHA-256:

`b123007660dbf5974c55b3a7490a80e9923594d2d3d42be04214b08bd70449db`

Standalone cumulative forward IPS SHA-256:

`37ee4a03138b0738d4e94053e6c16d1df75aacf28712ec3cfe8fcd7c55a37c9a` (**17,529 bytes**).

Only **98 ROM bytes differ from v23**, confined to the new helper/table/English phrase, one diagnostic record and the JSR call. All 479 indexed pointer values, untouched record bodies, game header, previously verified English introduction and four gameplay menu commands are unchanged. Byte-exact reverse IPS restores the Japanese original. The reverse IPS remains **private/local**.

**112 local regression tests PASS**: 95 earlier tests plus 15 v26 ROM/instruction-level tests and two read-only Lua tracer tests. The small 6502 instruction runner validated pointer arithmetic for every one of the 30 indexes, but it is **not** a full emulator.

The source-only ZIP was also unpacked independently; regenerating the IPS with the clean ROM reproduced its exact SHA-256.

## Brief emulator handoff

1. On the exact clean Japanese game, replace the prior v23 sidecar with the **standalone v26 IPS**; never stack patches. Cold boot FCEUX.
2. Load `tools/fceux_v26_independent_dictionary_trace.lua`.
3. Confirm the Lua overlay's v26 fingerprint, then trigger one nearby LOOK/NPC response (the same kind of response that produced `D1` and `DD` in v24b). **Do not replay the full game.**
4. Return `SquareTomSawyer_v26_dictionary_trace.txt` (or overlay screenshot). A positive `BF0A` helper count alongside token dispatches shows the new lookup executed; pixel/text correctness is still a separate criterion. Avoid saving in this diagnostic version.

## Remaining work

This is a working **offline 30-entry dictionary architecture**, not a 160-token English translation. Extending the pointer table requires real control-code-compatible English token assignments, a source-accurate line/wrapping encoder and bulk reallocation of Bank 6. If 160 tokens do not fit the native single-byte namespace, implement a controlled escape/two-level grammar or ROM expansion. Preserve the user's preferred workflow: dump → translate/edit TSV → compress → bulk inject → selective QA.

No commercial ROM, original-data rollback, or copied translation dump is committed.
