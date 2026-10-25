# Step 27 — v23: 29 genuine one-byte native reference tokens

**Status: original-ROM offline PASS, 95 local tests. FCEUX runtime still pending.**

This version improves substantially on the earlier v22 native `03 index` probe. It converts *all* 237 existing two-byte references to one-byte tokens `D0–EC`, while continuing to use the ROM's original 6502 secondary-text reader and shared records. No new executable code cave, ROM expansion, Bank5 lookup or mapper change is required.

## Engine patch: two existing instruction spans

| CPU / file offset | Original bytes | New bytes | Effect |
| --- | --- | --- | --- |
| `EDE7` / `0x3EDF7` (4 bytes) | `C9 03 D0 06` | `C9 D0 90 06` | Treat bytes below D0 as ordinary glyph/control input and D0+ as one-byte shared-text tokens |
| `EDFD` / `0x3EE0D` (9 bytes) | `A9 00 85 F2 20 92 ED 85 F1` | `38 E9 CF 85 F1 A9 00 85 F2` | Compute native reference index as token − CF, without consuming an additional input byte |

All other fixed-bank instructions retain their original values. The existing resolver still looks up shared pointer `$8002 + 2*index`, skips two metadata bytes and streams characters. Tokens D0..EC resolve to shared entries 1..29. The original Bank6 indexed dialogue corpus contains **no ordinary source body bytes CE..FF** after excluding original reference-index operands, making the selected token range disjoint for the audited corpus.

## Exact-ROM corpus result

The source ROM is SHA-256 `ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb`. The project generator `tools/native_onebyte_tokens_v23.py`:

- Converts 237 valid `03,index` pairs in 479 Bank6 records, entirely and atomically.
- Preserves original two-byte record headers, record order, shared targets, pointer-table group delimiters and the sentinel `$BFF7`.
- Repackages the 479 records into **14,088 bytes instead of 14,325**, reclaiming precisely **237 real Bank6 bytes**.
- Recalculates all indexed pointers; 445 values move.
- Compares the old and new expanded byte stream for all **479 records**, including raw control bytes, and finds **479/479 logical matches**.
- Constructs a standalone cumulative IPS retaining the **user-accepted v1.7 English opening and LOOK/TAKE/DIG/ITEM menu**.
- Validates the exact reverse IPS against the original, leaving its commercial ROM bytes out of GitHub.

Patched ROM SHA-256: `27a3cd09f75714458929aaca3bee3c4777cdba9b1ee4cd89ebb2ab24f2c2394b`.

Forward IPS SHA-256: `ce2ca8501c5f8c0def49eda922c3bf1b7b777bfc5ed137971815e4a1100da034`.

**95 local regression tests passed** (81 prior + 14 new).

## Important runtime limits

This is a *real experimental interpreter modification*, not just a compression calculation. **However, runtime is not confirmed**: a control path may read other non-indexed Bank6 text with legacy `03,index` references or unused high bytes that are not included in the 479-record census; the 6502 execution and text progression also need an emulator check. The original reference count and logical equivalence alone do not prove FCEUX success.

The rest of Bank6 still contains untranslated Japanese. This is *not* the complete English patch and recovers only 237 bytes, not the 9–10 KiB needed for a full uncompressed English script. It validates a one-byte path for 29 existing phrases, rather than creating the additional 130+ new phrase entries.

## Rebuild and optional emulator smoke check

```powershell
py -3 tools\native_onebyte_tokens_v23.py "C:\path\Square no Tom Sawyer (Japan).zip" --out work\v23
py -3 -m unittest discover -s tests -v
```

The generated `Square_Tom_Sawyer_v23_29_OneByte_Tokens_EXPERIMENTAL.ips` applies **alone** to the exact original Japanese ROM. Never stack patches. To test, cold-boot FCEUX and verify the accepted English intro/menu, then view an easily accessible NPC or interaction response. A brief smoke test suffices; do not play the full game line by line. Do not reuse savestates from another patch and do not save in this diagnostic build.

## Next work

Map any unindexed calls to the original `03` path and the interpreter's remaining control codes. Then extend this now-proven **offline** one-byte dispatch method to a full-English-only token namespace with dedicated phrase pointer storage, safe Bank5/Bank6 access or RAM staging, and representative FCEUX tests. If dictionary access cannot fit safely, pursue mapper-aware text expansion. The production workflow remains script dump → translation database → bulk insertion → selective quality assurance.

No Japanese ROM, copied third-party translation dump, original-data rollback or other commercial game image is committed.
