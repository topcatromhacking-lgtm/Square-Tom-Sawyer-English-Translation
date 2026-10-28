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

## v30 user log — wrong runtime cartridge, not a pagination verdict

The user returned `SquareTomSawyer_v30_four_line_witness.txt` and reported **no new page**. The actual tracer observed **5,181 frames**, **18 primary dispatches**, **six 01** and **three 02** calls, and **nine correctly mapped dictionary-helper hits**; crucially **F0=0**. Its physical ROM fingerprint read **`00 00 00` at `0x1B876–0x1B878`**, whereas the intended v30 body requires **`02 01 F0`**. The fixed JSR at `EE0A` was correct. Therefore the test was run on the v27 body, or an equivalent stale/non-v30 cartridge. It **cannot prove the page control failed**. Do not reinterpret this negative observation as page-engine evidence.

A corrected user-facing package was independently generated against the user's exact source ROM archive, starting from the SHA-verified v27 cumulative IPS. The final v30 standalone forward IPS is **17,519 bytes**, SHA-256 `b5498f821198bd9d2a07a6943f4e1bb9594fe0faaf35e0ae6f1f1de5d7e23e15`, and its patched ROM SHA-256 is `d6865858e0baafeff19a88413ac8fc7fda5be54b682d6ed59af3e24d42170bb0`. The patched bytes at `0x1B876` are independently checked as `02 01 F0`. The forward IPS builds the expected ROM from the clean original; the reverse IPS exactly restores the original source. All 479 original Bank6 primary pointers, intro and menu spans remain preserved versus v27.

User handoff: source-free ZIP containing the standalone v30 IPS, private rollback, source SHA-checking `apply_v30_patch.py`, `MAKE_V30_ROM.bat` Windows launcher, unchanged v30 read-only Lua tracer, and a manifest. The launcher creates a **separately named** `Square_Tom_Sawyer_v30_FourLine_Test.nes` on the user's own PC (it does not ship the ROM), eliminating confusion with auto-applied v27 same-name IPS sidecars. This local patch generation is verified offline; **FCEUX rendering of the corrected ROM is pending**.
