# Step 37 — v28 bulk import + page/storage planning code

**2026-10-27 — source-only engineering checkpoint; no ROM patch produced.**

The repository previously documented the v28 bulk script audit but did not include its program in \`tools/\`. This commit introduces \`tools/bulk_script_audit_v28.py\` and synthetic source-free tests. It normalizes BlackPaladin's TL-before-[ED] format into the legacy v18 parser's after-[ED] representation, then imports the existing public \`000TL\` and \`001TL\` translation drafts only when explicitly requested, via the same source-locked \`script_pipeline_v18\` inventory/matcher. The full 520-record editable TSV remains private; no third-party translated script, Japanese ROM, save, or binary patch is committed.

### Run on Windows

\`\`\`powershell
py -3 tools\bulk_script_audit_v28.py "C:\path\Square no Tom Sawyer (Japan).zip" --download-public-drafts --out work\v28_private
\`\`\`

Alternatively pass \`--script path\to\file\` once per local TL draft. The original Japanese ROM is SHA-256 pinned to \`ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb\`.

The private output includes a source-authenticated 520-row master TSV, a 479-row review TSV with English text, estimated wrapped line counts and page counts, unknown-bracket markup, unsupported glyphs, and the original two-byte metadata and conservative 01/02/03 control evidence. A JSON file contains aggregate statistics and record-by-record placements into **virtual** 16 KiB slots.

**Interpretation:** A three-line window and a 20-character wrap are tested preview parameters from v27, *not* a proven pagination protocol or hard physical line limit. Native byte \`03\` consumes the following native-reference operand; it must not be miscounted as independent byte \`01\`/\`02\` control. Bytes \`04..0F\` are reported as unclassified, not rewritten.

The abstract allocator guarantees record boundaries in its projected slots, but **cannot assign ROM offsets or produce an IPS**. Original MMC1 has 16 occupied PRG banks; extra virtual slots are **not** proof of a mapper upgrade. Any real multi-bank implementation requires an explicit per-record bank mapping, runtime bank-switch proof, branch safety, paging behavior, and cumulative/rollback SHA checks. v27 remains the last real FCEUX-accepted patch.

### Next engineering gate

Trace actual runtime control handling for byte \`01\` and \`02\` with a read-only emulator witness, then reproduce one real page continuation without changing gameplay semantics. Separately identify a safe bank mapper/trampoline or in-ROM bank reclamation strategy before converting virtual placements into physical addresses. No sequential NPC-by-NPC translation QA is required.

### Public TL continuation anomaly

The actual upstream TL files contain **479 unique pointer/text records** (409 in \`000TL\`, 70 in \`001TL\`), but record **#152 at pointer \`$18144\`, text \`$1983D\`** ends with \`[BR]\` and lacks \`[ED]\`. The normalization keeps this entry, adds \`[NO_ED]\` as an explicit review flag, and never invents a runtime end or page command. This explains why simpler terminator-delimited parsing loses a translation candidate. The other 478 records contain \`[ED]\`. Neither \`[BR]\` nor \`[NO_ED]\` is encoded into the ROM by this audit.
