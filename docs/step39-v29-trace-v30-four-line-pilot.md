# Step 39 — user v29 trace accepted; controlled v30 fourth-line pilot

**2026-10-27.** The user returned `SquareTomSawyer_v29_pagination_witness.txt`, captured on a ROM executing the new English text.

## Actual observed evidence

The witness ran **8,478 frames**, observed **172** entry hits at `$EDE7`, **7** byte-`01` dispatches, **4** byte-`02` dispatches, **3** English ED–EF token dispatches and **51** secondary-reader entries. It recorded 11 low-control events. Three events in the already-proven English B6-356 sequence were:

| Frame | Control | Next primary ptr |
|---|---|---|
| 7117 | 02 | `$B862` |
| 7131 | 01 | `$B863` |
| 7164 | 01 | `$B865` |

The exact v27 body at CPU `$B860` is `EF 02 01 ED 01 EE 00`. The public TL draft corresponding to source pointer `$182E0` (published item #358; our indexed B6-356) renders:

```
The angel whispered.[BR]
[LN]
There's nothing[LN]
for you here.[ED]
```

**Cross-source conclusion:** the actual pilot, the input script tags and live pointer progression strongly support mapping `[BR] -> 02` and `[LN] -> 01`. They **do not yet prove** whether `02` waits for input, clears a full window, advances to a new page, or merely alters rendering state. The previous trace's one-line “v27 NOT confirmed (or ROM API unavailable)” is an unresolved fingerprint failure, not contrary runtime evidence: all 3 English tokens were dispatched and the control-pointer addresses match v27 exactly. The new v30 witness reports each physical-byte fingerprint discrepancy separately and also checks fixed-bank mapped instructions.

## v30 standalone diagnostic

`tools/pagination_pilot_v30.py` derives the v27 canonical reversible patch from the **exact SHA-locked original Japanese ROM**, preserves the 479 Bank6 primary pointers and 29 original shared phrase targets, moves the 3 v27 English phrase bodies two bytes to extend the independent dictionary table from 32 to **33** entries, and installs token `F0` for **PAGE FOUR TEST.**. It changes only B6-356's current diagnostic text body and reclaimed Bank6 dictionary data, keeping menu and intro patches intact. The new body is:

```
EF 02 01 ED 01 EE 02 01 F0 00
```

The last line is **deliberately non-story text** to test page continuation beyond three visible lines. The builder generates cumulative forward and private rollback IPS from the clean original, with byte-identity checks. It is **not an emulator-validated ROM** yet. The original commercial ROM, modified ROM, and third-party translations are never committed.

The new read-only `tools/fceux_v30_four_line_witness.lua` records F0 execution, mapper-correct BF0A helper execution, dictionary index-33 pointer correctness, byte-01/02 dispatches and per-byte ROM fingerprint differences. It reports `SquareTomSawyer_v30_four_line_witness.txt`. Runtime F0 alone is not enough: the user must visually check whether the fourth line occupies a cleared/advanced page, overwrites content, fails to appear, or clips.

### Single reproducible test

Build from the clean original Japanese ZIP:

```powershell
py -3 tools\pagination_pilot_v30.py "C:\path\Square no Tom Sawyer (Japan).zip" --out work\v30
```

Apply **only** the generated standalone `Square_Tom_Sawyer_v30_FourLine_Pagination_DIAGNOSTIC.ips` to the clean original ROM (do not stack with v27); launch FCEUX and then `tools\fceux_v30_four_line_witness.lua`. Trigger the same already-known nearby LOOK/NPC dialogue. Inspect **PAGE FOUR TEST.** and report whether it appears on a new page or overlaps/does not appear. Save the witness text. Do **not** save over permanent game progress with this intentionally inaccurate test dialogue.

## Next gate after visual confirmation

If page continuation works, implement approved English paging semantics into the private TSV pipeline and advance to controlled bulk compression/real-bank allocation. If not, inspect `02` control handler and text window update state before changing more ROM code. In either case, preserve indexed and native-reference semantics; do not ask for a line-by-line gameplay translation.
