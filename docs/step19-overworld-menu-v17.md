# v1.6 FCEUX acceptance + v1.7 English overworld menu

## v1.6 visually verified — 2026-10-24

User provided eight FCEUX screenshots showing English opening dialogue including:

- PIRATE TREASURE / IS HIDDEN IN TOWN.
- REALLY?
- JIM! AMY! HURRY! / THE BOAT'S LEAVING!
- HUCK! I'M COMING!
- SORRY, TOM! / ONLY THREE TICKETS.
- TOM! WAKE UP! / YOU'VE SLEPT ENOUGH!

The screenshots also show the outdoor landscape and an indoor scene with an intact gameplay menu following the translated introduction. Multiple character portraits, English punctuation and two-line dialogue layout appear correct. **v1.6 PASSED for the supplied frames and scene transition.** The user did not supply screenshots of every single one of the twelve intro records, so do not claim individual frame-by-frame confirmation for unseen records. No assertion about full first-quest completion or saving.

## v1.7 concrete engineering breakthrough

The four basic overworld commands are **not indexed dialogue strings**. They are a static layout of **direct CHR tile indices**, stored in fixed PRG bank 15. The exact locations and modified values are corroborated by the historical Translation 2.0 patch without stacking that patch or copying its binary into our release:

| ROM offset | Original direct tile sequence | v1.7 menu | New tiles |
| --- | --- | --- | --- |
| 0x3D1AF | A3 BE B4 7E C0 | LOOK | E9 EC EC E8 FF |
| 0x3D1B6 | AB C0 FF FF | TAKE | F1 DE E8 E2 |
| 0x3D1BF | FF B5 C0 | DIG | E1 E6 E4 |
| 0x3D1C8 | CE CF E0 EE | ITEM | E6 F1 E2 EA |

CHR tile for a Latin letter is its canonical v1.6 input character code plus `0x70`. Thus Latin `A=6E` uses tile `DE`, `L=79` uses tile `E9`, and so on. The four menu arrays total exactly **16 changed bytes**; no original dialogue, menu behavior code, or loader routine is altered. DIG uses the existing left padding tile to fit a three-letter translation while preserving its terminating `01` byte at 0x3D1C2.

## v1.7 status and source

`tools/build_overworld_menu_v17.py` generates a new **standalone cumulative patch** from the original Japanese ROM. It first reproduces the exact verified v1.6 output SHA-256 `9709c1df01b9fb304ee9dd39f5dd48afe43aaf346827b83f9ab353dd18cae4ba` and the v1.6 IPS SHA-256 `b96f5b34816439d24437ea816f66004c878bb75b0ee55c7b63c48624fba2f06e`, then adds four disjoint overworld tile-array changes. **Never stack v1.6 and v1.7 manually**.

On the exact Japanese source ROM SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`, the final v1.7 ROM SHA-256 is `5d869aa02c3c72cb06cefedd159e77f30d7cc18f630d7e1a4356ffaa94e7d34d`. Forward IPS is **868 bytes**, SHA-256 `06d43967e663cf28b08867f87be25ff3f72a5f76c49ccf7eabd1fe27b76eced2`. Byte-exact rollback restores the Japanese original. Eight menu-specific tests passed locally, including an exact original-ROM integration check; the latter is skipped by source-free CI.

**FCEUX visual status for v1.7: PENDING.** This may reveal layout/visual problems that cannot be established from the ROM checks.

## User's targeted test

Remove prior `.nes.ips` sidecar. Put **v1.7** forward IPS renamed `Square no Tom Sawyer (Japan).nes.ips` alongside a clean Japanese source ROM, then cold-boot FCEUX New Game. Confirm opening behaves as v1.6, transition to outdoor gameplay, and inspect all four English menu choices LOOK / TAKE / DIG / ITEM. Move the selection and execute LOOK and ITEM. Send one screenshot plus any behavior glitches. Avoid saving in this diagnostic build; additional Japanese text remains untranslated.

## Next scope

After v1.7 runtime confirmation: in-game interaction results, item/inventory, battles, first town NPCs and the rest of the introductory event scripts. Continue to treat arbitrary bank6 relocation/expansion as a distinct risk requiring runtime validation.
