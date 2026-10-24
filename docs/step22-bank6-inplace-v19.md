# v1.9 — Bank 6 script-structure audit and guarded batch injection

**2026-10-24. Source-only/offline milestone. No new FCEUX-confirmed NPC dialogue yet.**

## Why this version exists

The user correctly requested a conventional ROM-translation workflow: **extract -> align published English draft -> edit and approve -> encode -> allocate/insert -> patch -> selective QA**. Version 1.8 already inventories 479 pointer-indexed records in Bank 6 and 41 in Bank 8, with local private TSV exports. It deliberately blocked all Bank 6 insertion while speaker/metadata bytes and pointer safety remained unclear.

Version **1.9** removes that blanket blocker for a **conservative subset**, without claiming the full ~10 KiB overflow is solved.

## Source-ROM findings

The exact Japanese ROM has 479 Bank 6 records; all source records are terminated by byte `00`. Each known record begins with at least two bytes that must be treated as metadata rather than ordinary dialogue characters. The two historical English IPS patches generally preserve these header bytes when substituting English; this supports a preservation strategy but does **not** prove the complete bytecode semantics.

| Original pointer group | Indexed records | `00 00` headers | Other two-byte headers |
| --- | ---: | ---: | ---: |
| 1 | 251 | 36 | 215 |
| 2 | 35 | 7 | 28 |
| 3 | 123 | 74 | 49 |
| 4 | 70 | 70 | 0 |
| **Total** | **479** | **187** | **292** |

The 292 other headers include combinations such as `2B 00`, `0B 01`, `0C 0D`, `23 00`. Their interpretation and any embedded controls remain to be verified. The 187 `00 00` entries are **structural candidates**, not 187 independently runtime-certified safe dialogue replacements.

Important: the apparent gap preceding Bank 6's text (`0x18412..0x18811`) contains additional non-text data. The bytes after the indexed text's end at `0x1C007` are also populated. Do not treat those areas as free space or allow in-place text to spill outside its record.

## New batch injector

`tools/script_pipeline_v19.py` consumes the *same* v1.8 private editable TSV and the checksum-verified original ROM. It can, in one command, insert **any number of separately approved `00 00`-header entries** as long as each English record fits its own original allocation. It:

- Preserves both leading metadata bytes and all existing 479 Bank 6 pointers.
- Uses the strict project English byte encoder and a trailing `00` terminator.
- Uses zero padding only inside an approved entry's own allocation.
- Refuses missing approval, unsupported glyphs, overflow, edited source-derived metadata, unexpected original ROM hashes, complex headers, changed surrounding bytes and overlapping edits.
- Retains the already FCEUX-accepted v1.7 English opening and LOOK/TAKE/DIG/ITEM commands, plus approved Bank 8 changes from v1.8.
- Generates a standalone cumulative forward IPS and an exact rollback, the latter **locally only**, never committed because it contains source-derived bytes.

There is **no automatic approval** of third-party translation drafts.

## Run locally

Use `tools/script_pipeline_v18.py dump` to create/edit your **ignored private** translation TSV:

```sh
python tools/script_pipeline_v18.py dump "/private/Square no Tom Sawyer (Japan).zip" --out work/script/master_PRIVATE.tsv --seed-opening
```

For metadata and candidate-fit analysis:

```sh
python tools/script_pipeline_v19.py audit "/private/Square no Tom Sawyer (Japan).zip" work/script/master_PRIVATE.tsv --out work/v19/audit.json
```

After reviewing and setting `status=approved` on one or more eligible Bank 6 TSV records:

```sh
python tools/script_pipeline_v19.py build "/private/Square no Tom Sawyer (Japan).zip" work/script/master_PRIVATE.tsv --out work/v19
```

The output IPS is `work/v19/Square_Tom_Sawyer_Bulk_Bank6_Inplace_v19.ips`. It is applied **alone** to the untouched Japanese original; do not stack v1.7 or v1.8 patches.

## Verification

Local tests: **32 total PASS** for the bundled source-only/ROM integration suite (20 v1.7–v1.8 plus 12 v1.9). On the exact original ROM, the integration test confirms that inserting a deliberately synthetic short English test string changes only the selected 7-byte Bank 6 allocation. All other Bank 6 bytes, pointer table, v1.7 translated intro/menu and ROM size remain unchanged; reverse IPS restores the exact original SHA-256.

**Do not distribute or use synthetic `HI` test dialogue as a translation release.** The test only verifies structural injection. No Bank 6 replacement has yet passed FCEUX gameplay QA.

## Next engineering milestone — v2.0 allocator research

Rather than play the game in order, analyze the unknown metadata/header family, dialogue interpreter, dictionary and bank-switch logic. Develop a text allocator that supports long English entries and pointer relocation with complete bank-aware validation. For the game's 520 identified indexed strings, integrate BlackPaladin's available translations from the pointer-matched private TSV. Continue discovering unindexed battle, menu, item and dictionary strings separately. Only then seek representative FCEUX smoke tests.

**Caution:** v1.9 is in-place-only and cannot inject the majority of longer English drafts. This is an explicit limit, not a silent data-corruption workaround.
