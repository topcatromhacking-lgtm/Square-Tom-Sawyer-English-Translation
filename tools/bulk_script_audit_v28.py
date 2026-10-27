#!/usr/bin/env python3
"""v28 source-locked private script import, paging review and virtual bank plan.

This is an AUDIT, not a ROM patch or an assertion that page controls are known.
External translated scripts and the copyrighted original ROM stay outside Git.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from analyze_rom import read_source
from english_codec_v15 import CHAR_TO_BYTE
import script_pipeline_v18 as v18
import build_opening_v16 as v16

SOURCE_SHA = v18.SHA
DRAFT_FILENAMES = ("tomsawyer_script_000TL.txt", "tomsawyer_script_001TL.txt")
DRAFT_ROOT = "https://raw.githubusercontent.com/BlackPaladin2022/Dumped-Scripts/main/"
DRAFT_DIR = "(NES) Square no Tom Sawyer MIX"
REVIEW_COLUMNS = (
    "id", "ptr_at", "text_at", "status", "english", "wrapped_preview",
    "line_count", "estimated_pages", "possible_overflow", "unsupported_chars",
    "unresolved_markup", "prefix_hex", "native_ref_count", "byte_01_count",
    "byte_02_count", "low_bytes_unclassified", "notes",
)
WIDTH = 20                # v27 demonstrated 20; not an engine-wide guarantee
LINES_PER_PAGE = 3        # three lines observed in v27; continuation unproven
VIRTUAL_BANK_SIZE = 0x4000
BANK6_ORIGINAL_CAPACITY = v18.BANK6_END - v18.BANK6_FIRST


def download_drafts(directory: Path) -> list[Path]:
    """Opt-in network fetch to PRIVATE output; never bundle the texts."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for filename in DRAFT_FILENAMES:
        url = DRAFT_ROOT + quote(DRAFT_DIR + "/" + filename)
        with urllib.request.urlopen(url, timeout=25) as response:
            data = response.read(1_000_001)
        if len(data) > 1_000_000 or b"//POINTER #" not in data:
            raise ValueError(f"Unexpected public draft response: {filename}")
        path = directory / filename
        path.write_bytes(data)
        paths.append(path)
    return paths


def normalize_tl_draft(path: Path, private_dir: Path) -> Path:
    """Adapt upstream TL text-before-[ED] into the older v18 parser format.

    v18.references() expects English prose AFTER [ED] as in annotated source
    dumps. Upstream *TL.txt files instead store translated text BEFORE [ED].
    Do not silently feed those files into v18 or all drafts look empty.
    """
    contents = path.read_text(encoding="utf-8-sig")
    matches = list(v18.SCRIPT_PTR_RE.finditer(contents))
    if not matches:
        raise ValueError(f"No pointer records in TL script: {path.name}")
    lines = []
    for index, match in enumerate(matches):
        segment = contents[match.end():matches[index + 1].start()
                           if index + 1 < len(matches) else len(contents)]
        body = re.search(r"#W16\(\$[0-9A-Fa-f]+\)\s*(.*?)\[ED\]",
                         segment, flags=re.I | re.S)
        if not body:
            raise ValueError(f"Missing TL text/terminator at {path.name} #{index}")
        # [null] in the published TL is a formatting marker, not a glyph.
        # The original record's two metadata bytes remain in the TSV.
        english = re.sub(r"\[null\]", "", body.group(1), flags=re.I)
        english = " ".join(english.splitlines()).strip()
        lines.append(match.group(0) + "\n[ED]\n" + english + "\n\n")
    private_dir.mkdir(parents=True, exist_ok=True)
    result = private_dir / (path.stem + "_normalized_PRIVATE.txt")
    result.write_text("".join(lines), encoding="utf-8")
    if len(v18.references(result)) != len(matches):
        raise AssertionError("TL normalization dropped pointer records")
    return result


def normalized_sources(paths: list[Path], private_dir: Path) -> list[Path]:
    return [
        normalize_tl_draft(path, private_dir)
        if path.name.lower().endswith("tl.txt") else path
        for path in paths
    ]


def wrapped_lines(text: str, width: int = WIDTH) -> tuple[list[str], list[str]]:
    """Make a conservative non-destructive PREVIEW, not runnable control bytes.

    Existing [LN] markers are treated as requested line boundaries. Any other
    bracket markup remains visible and is separately flagged for human review.
    Long unbreakable words are NOT silently split.
    """
    if width < 1:
        raise ValueError("Invalid preview width")
    if not text:
        return [], []
    explicit = re.sub(r"\[LN\]", "\n", text.replace("\\n", "\n"), flags=re.I)
    pages = []
    warnings = []
    for segment in explicit.split("\n"):
        words = segment.split()
        if not words:
            warnings.append("empty explicit line")
            continue
        line = ""
        for word in words:
            if len(word) > width:
                warnings.append(f"word wider than {width}: {word[:36]}")
            if line and len(line) + 1 + len(word) > width:
                pages.append(line)
                line = word
            else:
                line = (line + " " + word) if line else word
        if line:
            pages.append(line)
    return pages, warnings


def control_audit(raw: bytes) -> dict:
    """Count bytes conservatively; skip the operand of native 03,index."""
    if len(raw) < 3 or raw[-1] != 0 or 0 in raw[2:-1]:
        raise ValueError("Invalid source dialogue record")
    counts = Counter()
    body = raw[2:-1]
    i = 0
    while i < len(body):
        byte = body[i]
        if byte == 3:
            if i + 1 >= len(body) or not 1 <= body[i + 1] <= 29:
                raise ValueError("Malformed original native reference")
            counts["native_refs"] += 1
            i += 2
        else:
            if byte in (1, 2):
                counts[f"byte_{byte:02X}"] += 1
            elif 4 <= byte <= 15:
                counts[f"unclassified_{byte:02X}"] += 1
            i += 1
    return {
        "prefix_hex": raw[:2].hex(),
        "native_ref_count": counts["native_refs"],
        "byte_01_count": counts["byte_01"],
        "byte_02_count": counts["byte_02"],
        "low_bytes_unclassified": ",".join(
            f"{k[-2:]}:{v}" for k, v in sorted(counts.items())
            if k.startswith("unclassified_")
        ),
    }


def review(rows: list[dict], width: int = WIDTH, height: int = LINES_PER_PAGE):
    if height < 1:
        raise ValueError("Invalid preview height")
    table = []
    counts = Counter()
    modeled_lengths = []
    for row in rows:
        if row["bank"] != "6":
            continue
        raw = bytes.fromhex(row["raw_hex"])
        evidence = control_audit(raw)
        text = row["english"]
        lines, warnings = wrapped_lines(text, width)
        unsupported = sorted({
            char for line in lines for char in line
            if (char.upper() if "a" <= char <= "z" else char) not in CHAR_TO_BYTE
        })
        markup = sorted(set(re.findall(r"\[[^\]]+\]", text, re.I))
                        - {"[LN]", "[ln]", "[Ln]", "[lN]"})
        line_count = len(lines)
        count_pages = (line_count + height - 1) // height
        counts["source_records"] += 1
        counts["draft_records"] += bool(text)
        counts["empty_drafts"] += not bool(text)
        counts["drafts_over_three_lines"] += line_count > height
        counts["drafts_with_unsupported_glyphs"] += bool(unsupported)
        counts["drafts_with_unresolved_markup"] += bool(markup)
        counts["source_native_references"] += evidence["native_ref_count"]
        counts["source_direct_01"] += evidence["byte_01_count"]
        counts["source_direct_02"] += evidence["byte_02_count"]
        counts["complex_headers"] += evidence["prefix_hex"] != "0000"
        # Deliberately uncompressed: page linebreaks and normal symbols only.
        # This is a STORAGE LOWER-LEVEL INPUT estimate, not native page encoding.
        size = 0 if not text else 3 + sum(map(len, lines)) + max(0, line_count - 1)
        modeled_lengths.append({"id": row["id"], "bytes": size, "page_count": count_pages,
                                "safe_to_inject": False})
        table.append({
            "id": row["id"], "ptr_at": row["ptr_at"], "text_at": row["text_at"],
            "status": row["status"], "english": text,
            "wrapped_preview": "\\n".join(lines),
            "line_count": str(line_count), "estimated_pages": str(count_pages),
            "possible_overflow": "YES" if line_count > height else "NO",
            "unsupported_chars": "".join(unsupported),
            "unresolved_markup": ",".join(markup),
            **evidence, "notes": "; ".join(warnings + ([row["notes"]] if row["notes"] else [])),
        })
    if len(table) != 479:
        raise ValueError("Expected 479 indexed Bank6 records")
    return table, dict(counts), modeled_lengths


def allocate_virtual_banks(lengths: list[dict], capacity: int = VIRTUAL_BANK_SIZE):
    """Pack record identities into abstract 16 KiB slots.

    NOT real physical bank locations, not a claim that MMC1 can address them.
    No patch or 16-bit pointer encoding is generated.
    """
    if capacity < 1:
        raise ValueError("Invalid bank capacity")
    placements, used = [], []
    seen = set()
    for rec in lengths:
        identity, size = rec["id"], rec["bytes"]
        if identity in seen or not isinstance(size, int) or size < 0 or size > capacity:
            raise ValueError(f"Unallocatable or repeated record: {identity}")
        seen.add(identity)
        if size == 0:
            placements.append({"id": identity, "slot": None, "offset": None,
                               "bytes": 0, "untranslated": True})
            continue
        if not used or used[-1] + size > capacity:
            used.append(0)
        slot = len(used) - 1
        offset = used[slot]
        used[slot] += size
        placements.append({"id": identity, "slot": slot, "offset": offset,
                           "bytes": size, "untranslated": False})
    return {
        "slot_bytes": capacity, "slots_used": len(used),
        "slot_occupancy": used, "placements": placements,
        "abstract_only": True, "actual_rom_offsets_assigned": False,
        "native_dialogue_pointer_table_rewritten": False,
        "bank_selection_hook_implemented": False,
        "mapper_expansion_verified": False,
    }


def build_audit(original: bytes, script_paths: list[Path], output: Path,
                width: int = WIDTH, height: int = LINES_PER_PAGE):
    output.mkdir(parents=True, exist_ok=True)
    master = output / "sts_v28_translation_master_PRIVATE.tsv"
    normalized = normalized_sources(script_paths, output / "draft_sources_PRIVATE")
    dump_report = v18.dump(original, master, normalized, True, None)
    rows = v18.load_edited(original, master)  # re-check all source identities
    table, counts, lengths = review(rows, width, height)
    review_file = output / "sts_v28_dialogue_review_PRIVATE.tsv"
    with review_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, delimiter="\t", fieldnames=REVIEW_COLUMNS,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(table)
    virtual = allocate_virtual_banks(lengths)
    # Never confuse this with the old 160-token heuristic: no compression here.
    stats = {
        "version": "v28-source-locked-private-bulk-audit",
        "source_sha256": SOURCE_SHA, "index_count": 520, "bank6_indexed": 479,
        "bank8_indexed": 41, "requested_width": width,
        "requested_lines_per_page": height,
        "width_and_pagination_semantics_verified": False,
        "translation_status": counts,
        "uncompressed_preview_symbol_bytes": sum(x["bytes"] for x in lengths),
        "original_bank6_indexed_capacity": BANK6_ORIGINAL_CAPACITY,
        "virtual_storage": virtual,
        "external_import": dump_report,
        "has_generated_ips": False,
        "note": "Planning only. Native page/continue codes, Bank6 crossing and "
                "runtime bank selection require separate source/runtime proof.",
    }
    json_file = output / "sts_v28_layout_audit.json"
    json_file.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    return stats


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path, help="Exact original Japanese ROM or ZIP")
    p.add_argument("--script", action="append", type=Path, default=[],
                   help="Public translated draft file already on disk (repeatable)")
    p.add_argument("--download-public-drafts", action="store_true",
                   help="Explicitly fetch the two public Bank6 TL files to PRIVATE work")
    p.add_argument("--out", type=Path, default=Path("work/v28_private"))
    p.add_argument("--width", type=int, default=WIDTH)
    p.add_argument("--lines-per-page", type=int, default=LINES_PER_PAGE)
    args = p.parse_args(argv)
    rom = read_source(args.source)  # same exact SHA gate as the v18 inventory
    scripts = list(args.script)
    if args.download_public_drafts:
        scripts += download_drafts(args.out / "draft_sources_PRIVATE")
    report = build_audit(rom, scripts, args.out, args.width, args.lines_per_page)
    summary = {k: v for k, v in report.items() if k != "virtual_storage"}
    summary["virtual_slots_used"] = report["virtual_storage"]["slots_used"]
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
