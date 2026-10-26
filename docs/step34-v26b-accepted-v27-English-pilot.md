# Step 34 — v26b live dictionary PASS; v27 accessible English dialogue pilot

**2026-10-26 — Engineering milestone. v26b is FCEUX runtime accepted. v27 is built and statically validated, but its rendered English remains unverified.**

## Verified user FCEUX log (v26b)

The submitted `SquareTomSawyer_v26b_live_bank_trace.txt` establishes **the correct independent phrase table, helper instructions and returned phrase pointer under live FCEUX**:

| Measurement | Result |
| --- | --- |
| Physical cartridge fingerprint | v26 verified |
| CPU helper at idle | other (`$31`) — not the active dialogue bank |
| Frames | 6,775 |
| Bank 6 text dispatcher hits | 84 |
| Native token hits | 1 (`$DD`) |
| CPU `$BF0A` execute-hook hits | 1 |
| **Bank 6 helper opcode bytes verified during actual hook** | **1** |
| Foreign/wrong-bank helper hits | **0** |
| **Dictionary pointer comparisons at `$EE1C`** | **1 MATCH, 0 MISMATCH** |
| Secondary text reader hits | 12 |
| Newly inserted English token `$ED` | 0 |

At **frame 5868**, the trace records `DISPATCH token=DD primary_next=B861`, followed by `BF0A helper=BANK6-VALID index=14 op=8C`, and `EE1C index=14 ptr=8894 expected=8894 result=MATCH`.

**Acceptance: independent Bank 6 dictionary lookup actually executes and resolves the correct target in FCEUX.** The idle mapper position is irrelevant to the at-hook check. This is *not* proof that an independent English phrase has been rendered on-screen.

## v27: target the dialogue that FCEUX already reached

Mapping the previous original ROM against the v23/v26 pointer-redistributed bank identifies CPU `$B861` as the byte *after the first token* in **B6-356**, group 3, current record CPU start `$B85E`. Its original Japanese text and the public draft translation align by source pointer field `0x182E0` / original text offset `0x1B951`.

The published English draft for this particular line is:

> The Angel whispered. There's nothing for you here.

The v27 diagnostic changes **only B6-356**, using three new genuine English phrase references stored in the independent Bank 6 dictionary:

| Token | Dictionary index | CPU text pointer | English phrase |
| --- | ---: | --- | --- |
| `$ED` | 30 | `$BF66` | THERE'S NOTHING |
| `$EE` | 31 | `$BF78` | FOR YOU HERE. |
| `$EF` | 32 | `$BF88` | THE ANGEL WHISPERED. |

B6-356's experimental record changes from a source `$DD` token to `EF 02 01 ED 01 EE 00` following the unchanged `00 00` prefix, preserving the original `02 01` separator and adding a new `01` line break. **On-screen layout and semantics of the controls must be tested**; the abstract English encoder has 20-character phrase limits but cannot establish renderer behavior.

All 479 original indexed dialogue pointer values remain unchanged relative to v23. All other 478 record bodies remain identical to v23. The separate dictionary retains the same first 29 shared targets and expands to 32 tokens. The original v26 unreachable B6-420 `HELLO` diagnostic is **not included** in v27. The English opening and menu are untouched.

The source/ROM integration tests confirm all those properties and an exact rollback to the Japanese original. **88 bytes** remain unused in the original Bank 6 237-byte reclaimed tail.

## Checksums and status

Original Japanese source SHA-256:

`ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`

v27 patched ROM SHA-256, used privately for testing (ROM **not** distributed):

`cd64be1a795409474ce98642177af56e9869ef10a36b4cc5f1cdd732b3f1053a`

Standalone cumulative v27 IPS SHA-256:

`a3bce22df8caf23a736817f9b20bda9d9676d4f8ec0b76c1f550ef9f1c958de1`

The 14 newly written tests for the v27 builder and read-only FCEUX Lua include original ROM SHA-gating, 479 unchanged dialogue pointers, all other 478 records unchanged, phrase bytes, line controls, source-v23 preservation, cumulative forward/rollback, and **simulated actual v27-ROM three-token execution**. The extracted v26/v27 source package passes **31 tests total**. This is an *offline result only* for v27.

## One short next emulator test

1. Apply the **standalone v27 IPS alone to the exact clean original Japanese ROM**. Do not stack patches with v23 or v26. Cold-boot FCEUX.
2. Load the v27 read-only `fceux_v27_english_pilot_trace.lua` from the supplied release ZIP. Trigger the **same reachable LOOK/NPC interaction that produced `$DD` and pointer `$B861`** in the earlier logs.
3. Return `SquareTomSawyer_v27_english_phrase_trace.txt` and briefly describe **whether the English text actually renders and where line breaks occur**. A screenshot is optional and not required.

Expected positive runtime result: **`$EF`, `$ED`, `$EE` each invoke the real helper and resolve matching dictionary pointers**, and FCEUX displays the English sentence. The trace is needed for execution, the player's observation for visual fidelity. New game progress in sequence is unnecessary.

## Subsequent work

Once one accessible English phrase is rendered reliably, enlarge the phrase dictionary and test bulk translation against the full private 520-record TSV and complete control-code inventory. The present 32-token diagnostic does **not** translate all of Bank 6 or prove that 160 one-byte token values are safe.

No commercial ROM, full original script, historical patch binaries or source-derived rollback data is committed to GitHub.
