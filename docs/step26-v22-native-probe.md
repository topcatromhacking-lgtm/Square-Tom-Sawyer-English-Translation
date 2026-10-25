# Step 26 — Native reference substitution probe and fixed-bank decoder survey

**2026-10-24 — v22 offline result; no new English gameplay build and no new one-byte token decoder.**

## Validated ROM-level experiment

The original Japanese ROM (SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`) uses `03 <index>` for shared text references. The 29 referenced records form a shared dependency set; adding another reference *inside* those target records would introduce unsafe nesting.

We searched 479 indexed Bank 6 records for **existing literal copies** of any of the 29 referenced phrases, using a conservative rule: simple `00 00` record metadata; no existing `03` and no low-valued embedded controls in the candidate body; no modifications to the 29 referenced records.

This restrictive scan found **one** qualified example: **B6-420** at ROM offset `0x1BE6A` is seven bytes long and has a four-byte body that exactly duplicates reference target **B6-000** (native index 1).

The v22 diagnostic modifies this single record using `03 01` plus its original zero terminator and trailing zero padding. An independent single-level text expander confirms that this new record yields precisely the original visible bytes. **All 479 indexed pointers remain unchanged**, including the `FFFF` delimiters. The cumulative IPS retains the already user-accepted v1.7 English opening and LOOK/TAKE/DIG/ITEM menu.

Original ROM bytes outside this record and the existing v1.7 patch are unchanged. Forward and byte-exact rollback verification PASS. The v22 patch adds only **four changed bytes** relative to v1.7. It claims **zero bytes reclaimed in the physical Bank 6 allocation**; repacking could theoretically reclaim two, but that is not attempted here. **FCEUX execution of the new reference is not yet verified.** Because reaching B6-420 could require lengthy play, this probe is not assigned as a mandatory user gameplay test.

## Why this does not solve whole-script compression

The game's `03 index` control needs two bytes, not one. The stringent duplicate-literal search exposes only one nonnested case and therefore cannot provide a 144–160-token library. The separate v21 flat-phrase experiment remains a theoretical compression feasibility estimate, not a working NES codec.

## Fixed-bank 6502 audit

`tools/decoder_hook_survey_v22.py` validates byte signatures in the original fixed PRG bank:

- `$EDC2` — original Bank 6 text-read wrapper (switches via `$C3D4`).
- `$EDE7` — original `03` reference dispatch.
- `$EDFD` — original indexed reference resolver.
- `$EE50` — character-to-CHR conversion.
- `$EDCD` / `$7980` — reference state dispatch.

Raw call-byte occurrences include `JSR $EDC2` at `$CB9F`, `JMP $EDC2` at `$C057`, and three `JSR $EE50` sequences at `$ED65`, `$EDF1`, and `$EE44`. These are ROM byte-pattern findings; not every appearance is guaranteed code without control-flow proof.

The long zeros at `$E750` (27 bytes), `$E86F` (24 bytes), and repeated 32-byte FF runs around `$EBED–$ECAD` occur in structured data. **No safe executable cave in fixed Bank 15 has been established**. Bank 5's apparent dictionary storage cannot be read concurrently with Bank 6 without a bank switch, RAM staging, or other architectural change.

## Test and release scope

Local integrated source snapshot: **81 passing tests** (67 previous + 14 new v22). Source code, regression tests, manifest and diagnostic cumulative IPS are packaged, **without** commercial ROM images, third-party dumps or source-derived rollback files. The source-gated build can regenerate the exact rollback locally.

## Next engineering target

A new one-byte token codec requires (a) source-verified text/control grammar and collision-free codepoint selection for an entirely English Bank 6, (b) confirmed fixed-bank hook space and 6502 call-path safety, and (c) proven Bank 5 dictionary access or safe RAM staging. Implement **one true one-byte token expansion** in a running emulator, then automate compressed bulk insertion. If it cannot satisfy MMC1 and RAM constraints, use controlled text-bank expansion rather than declaring compression complete.

The user does not need to play through the game to discover each line; the intended workflow remains dump → translation database → encode/compress → guarded injection → representative FCEUX checks.
