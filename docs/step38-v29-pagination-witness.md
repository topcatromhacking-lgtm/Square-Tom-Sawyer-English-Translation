# Step 38 — v29 read-only native control witness

The public translated Bank6 TL files contain 479 unique pointer/text identities. 478 records include an \`[ED]\` terminator; source record #152 at \`$18144 / $1983D\` has a trailing \`[BR]\` but no \`[ED]\`. The upstream files contain **1,048 \`[LN]\`**, **108 \`[BR]\`**, **50 \`[04]\`** and **13 \`[05]\`** markers (plus \`[null]\` formatting markers). These are author/script tags; the mapping to the game's native runtime opcodes has **not** yet been demonstrated.

The v27 game displayed the English record B6-356 correctly using source bytes \`EF 02 01 ED 01 EE 00\`. That proves an English sentence and its line layout, but cannot alone distinguish an ordinary new line, a page break, or a continuation control in the generic text state machine.

\`tools/fceux_v29_pagination_witness.lua\` is therefore the next small verification gate. Launch it in **FCEUX with standalone v27 ROM already loaded**, at the current gameplay position. It fingerprints physical patched bytes, reads the control dispatch at \`$EDE7\`, records counts for \`00/01/02/03\`, and logs snapshots of \`$F5/$F6\`, \`$F7/$F8\`, \`$F1\` and \`$7980/$7981\` for up to 320 deduplicated events. It also counts secondary-reader execution at \`$EE2C\`.

Output: \`SquareTomSawyer_v29_pagination_witness.txt\`, updated every 120 frames and on emulator exit. The tracer does not write to RAM, ROM, saves, input, or emulator state. Existing progress may be used; no reset, new IPS, or repeat of the v27 lookup witness is needed.

**Limit:** the log is observable evidence, not a proof of pagination semantics by itself. The remaining implementation needs to correlate 01/02 dispatch with physical screen clearing/continuation and inspect the original fixed-bank control handler, then perform one reversible page-advance proof. Until then, \`[BR]\`, \`[04]\` and \`[05]\` remain opaque, and the v28 virtual-bank planner cannot emit real text pointers or a bulk translation IPS.
