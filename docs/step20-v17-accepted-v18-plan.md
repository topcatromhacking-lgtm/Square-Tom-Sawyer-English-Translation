> **SUPERSEDED — 2026-10-24:** The user correctly challenged this sequential field-menu → combat → town playthrough order. We now use the [v1.8 script pipeline](step21-dump-translate-inject-pipeline.md) instead: dump all identifiable scripts, align translations, bulk encode, allocate/repoint, patch, and run representative QA. Treat the old per-screen timeline below only as a list of test areas, not the development schedule.

# Step 20 — v1.7 accepted; vertical-slice roadmap (2026-10-24)

## Accepted hardware/emulator evidence

The user confirms that the four overworld menu commands **LOOK / TAKE / DIG / ITEM** are translated and display correctly in FCEUX, with "All good." Mark **v1.7 visual PASS**, in addition to the already verified v1.6 cutscene + transition. The user has not separately documented all item submenus and interaction-result messages, so these remain the next targets. Preserve the successful v1.7 code, source ROM SHA-256 guard and reversible patch chain as regression baseline.

## Phase-gated development plan

| Build | Scope | Evidence required |
| --- | --- | --- |
| **v1.8 — FIELD & ITEM** | Identify in-ROM text storage for command result messages, location/interaction feedback, ITEM submenu headers/commands; translate a **specific reproducible route** from the outdoor scene into the house and back. Distinguish direct CHR tile tables from indexed text. | One cumulative clean-ROM IPS; byte-change whitelist, exact rollback, command navigation and screenshot of at least one action response and ITEM window in FCEUX. |
| **v1.9 — BATTLE** | Inventory combat command labels, feedback text, item/ability names and first encountered enemy names. Update fonts/strings only through identified mappings. | Play one full combat sequence, use at least one choice, finish encounter and return to exploration without text/window regressions. |
| **v1.10 — BANK 6 RELOCATION** | Introduce relocated Bank 6 English records with verified access semantics and guarded pointer references; allocate additional space or expand mapper-aware PRG if demonstrated necessary. Earlier snapshot: 374/479 candidates exceed individual allocations, minimum positive overflow approx 10,070 bytes. | Exact translation encoder, full offset/pointer inventory, record-boundary checks, emulator confirmation of relocated actual NPC dialogue, and reversible patch. |
| **v1.11 — TOWN & FIRST QUEST** | Build continuous narrative route: opening, overworld, town NPCs, first quest, item and battle interactions, using the verified capacity solution. Reuse historic scripts with editorial review and attribution. | Reproducible first-quest walkthrough/checkpoints, not disconnected screens; verify save/load once state handling is known. |
| **v2.0 target — FULL TRANSLATION** | Complete remaining event/NPC dialogue, battle/menu/item strings, endings, quality checks and release credits. | Full-game playthrough, stable patch, documentation; original ROM never distributed. |

## Engineering rules

1. Every build is **cumulative, but the user applies only the latest IPS to the exact untouched original ROM**; never stack intermediate patches.
2. Only change code/data after confirming byte ownership; preserve functioning font uploads and verified v1.6 event pointers. Avoid another speculative loader patch.
3. Maintain explicit distinction between source-only tests, emulated gameplay, and user-verified screenshots.
4. Do not commit Japanese ROM, historical third-party IPS binaries, third-party raw script dump or source-derived rollback glyph bytes to the public repository.
5. Keep tests within a coherent playable route so interaction/menu/battle regressions show up early. Prefer a compact test instead of an extended list of unrelated screens.

**Immediate next engineering input needed from user: none.** The verified ROM, two historical IPS patches, current source code and references have already been made available. User help will be needed for FCEUX once an actual v1.8 cumulative patch is ready.
