# Step 30 — v24b FCEUX trace: v23 Bank 6 token execution confirmed

**Date:** 2026-10-25. **Input:** User-uploaded `SquareTomSawyer_v24b_token_trace.txt` from an actual FCEUX run.

## Exact measured results

| Measurement | User's v24b report |
| --- | --- |
| Cartridge ROM v23 fingerprint | **true / v23** |
| CPU mapped decoder fingerprint | **v23** |
| Number of fingerprint rechecks | **118** |
| Elapsed frames | **7,032** |
| Bank 6 decoder dispatches at CPU `$EDE7` | **107** |
| Token candidates `$D0–$EC` | **2** |
| Token resolver executions at `$EDFD` | **2** |
| Secondary reader executions at `$EE2C` | **21** |
| Unexpected input bytes `$ED–$FF` | **0** |
| Reported status | **TOKEN PATH EXECUTED (VISUAL OUTPUT STILL TO CHECK)** |

The trace independently identifies these two token/resolver pairs:

- Frame **6117**: dispatch `A=D1`, followed by resolver `A=D1`, native shared target **B6-001**.
- Frame **6765**: dispatch `A=DD`, followed by resolver `A=DD`, native shared target **B6-013**.

## What is accepted

**The experimental v23 one-byte token path executes in real FCEUX.** The correct decoder bytes are visible both in the emulated cartridge and mapped CPU memory. Dispatch and resolver counts agree for the two encountered token bytes. Secondary-reader execution occurs and there are no reported unexpected `>=ED` bytes during this run.

This is the first actual **Bank 6 runtime code-path evidence** for v23, beyond its earlier Bank 8 English introduction smoke test. The original, incorrect v24 `$EDE7=$00` startup fingerprint is superseded by this live v24b evidence; do not interpret its zero counters as proof of failure.

## What is *not* accepted yet

- We have **not independently checked screenshots or compared pixels/strings** for the two expanded Japanese dialogue instances, so *visual glyph/text fidelity remains pending*.
- The report hits **2 of 237** converted references and 2 of 29 possible token values; it does not prove every possible reference/caller path.
- `secondary reader=21` is a count of code execution events, not 21 verified successful token expansions.
- Nothing in this trace establishes the feasibility of **144–160 additional English phrase entries**, their pointer-table allocation, remaining control-byte grammar, bank mapping, or a full English ROM.

## Engineering priority after the acceptance

1. Preserve the proven v23 decoder patch, the two live token examples, and the v1.7 English opening/menu baseline as regression fixtures.
2. Use the existing 520-row source-locked private TSV to design a single-byte English-specific token namespace and stable phrase IDs; do not overwrite existing indexed NPC records to create extra dictionary entries without proving the references.
3. Develop verified storage and memory-mapping for an expanded dictionary and decoder; compare original-vs-compressed **decoded text streams** and enforce real line/control widths, not only theoretical character counts.
4. Build a source-verified reversible cumulative English pilot that uses the new dictionary engine; request **one short visual FCEUX smoke** only when it can verify an actual newly compressed English sentence.
5. Maintain the production workflow: **dump → match/review existing translations → encode/compress → bulk patch → selective runtime QA**. No sequential gameplay-based translation.

**Current status:** v23 native one-byte token interpreter **runtime path PASS** (two token/resolver pairs). Full rendered-text fidelity and expanded English dictionary are still **unverified**. No need to rerun v24/v24b for startup checks.
