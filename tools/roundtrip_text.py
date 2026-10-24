#!/usr/bin/env python3
"""Lossless, source-verified inventory/roundtrip of indexed script bytes.

This does NOT decode, translate, expand, or safely reinsert changed text.
The local extraction JSON contains copyrighted game-derived bytes: keep it out
of Git and do not distribute. The default command emits no modified ROM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from analyze_rom import read_source, get_record_map

SCHEMA = "square-tom-sawyer-raw-dialogue-v1"


def extract(data: bytes) -> dict:
    records, summary = get_record_map(data)  # checks exact base ROM identity
    entries = []
    for meta in records:
        start = int(meta["text_file_offset"], 16)
        raw = data[start:start + meta["length_bytes"]]
        entries.append({
            "index": meta["global_index"],
            "group": meta["group"],
            "pointer_file_offset": meta["table_file_offset"],
            "text_file_offset": meta["text_file_offset"],
            "byte_length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_hex": raw.hex(),
        })
    return {
        "schema": SCHEMA,
        "base_rom_sha256": hashlib.sha256(data).hexdigest(),
        "description": "PRIVATE: source game encoded bytes, NOT decoded dialogue",
        "group_counts": summary["group_counts"],
        "entries": entries,
    }


def reconstruct(data: bytes, extracted: dict) -> bytes:
    """Identity-only repack: reject ANY mismatched edited or incomplete entry."""
    records, summary = get_record_map(data)
    if extracted.get("schema") != SCHEMA:
        raise ValueError("Wrong extraction schema")
    if extracted.get("base_rom_sha256") != hashlib.sha256(data).hexdigest():
        raise ValueError("Base ROM fingerprint mismatch")
    if extracted.get("group_counts") != summary["group_counts"]:
        raise ValueError("Group inventory mismatch")
    if len(extracted.get("entries", [])) != len(records):
        raise ValueError("Incomplete record inventory")

    new = bytearray(data)
    for i, (item, meta) in enumerate(zip(extracted["entries"], records)):
        if item.get("index") != i or item.get("group") != meta["group"]:
            raise ValueError(f"Entry #{i}: index or group mismatch")
        if (item.get("text_file_offset") != meta["text_file_offset"] or
                item.get("pointer_file_offset") != meta["table_file_offset"]):
            raise ValueError(f"Entry #{i}: pointer or file offset changed")
        try:
            raw = bytes.fromhex(item["raw_hex"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Entry #{i}: invalid raw hex") from exc
        if len(raw) != item.get("byte_length") or len(raw) != meta["length_bytes"]:
            raise ValueError(f"Entry #{i}: byte length changed")
        if hashlib.sha256(raw).hexdigest() != item.get("sha256"):
            raise ValueError(f"Entry #{i}: record hash mismatch")
        start = int(meta["text_file_offset"], 16)
        if raw != data[start:start + len(raw)]:
            raise ValueError(f"Entry #{i}: contents no longer match source")
        if raw[-1] != 0:
            raise ValueError(f"Entry #{i}: terminator is not zero")
        new[start:start + len(raw)] = raw

    result = bytes(new)
    if result != data or hashlib.sha256(result).hexdigest() != extracted["base_rom_sha256"]:
        raise ValueError("Reconstructed ROM is not byte-identical")
    return result


def statistics(extracted: dict) -> dict:
    entries = extracted["entries"]
    counts = Counter()
    for entry in entries:
        counts.update(bytes.fromhex(entry["raw_hex"]))
    return {
        "indexed_records": len(entries),
        "groups": extracted["group_counts"],
        "total_bytes": sum(e["byte_length"] for e in entries),
        "unique_byte_values": len(counts),
        "frequent_byte_values": [
            {"byte": f"0x{value:02X}", "count": count}
            for value, count in counts.most_common(20)
        ],
        "note": "Byte values are not assigned glyph/control meanings; counts include metadata and terminators.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="Original Japanese ROM (.nes or ZIP containing it)")
    parser.add_argument("--out", type=Path, default=Path("work/text-roundtrip"),
                        help="PRIVATE output directory under ignored work/")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    data = read_source(args.rom)
    extracted = extract(data)
    # Identity reconstruction BEFORE writing any output.
    assert reconstruct(data, extracted) == data
    (args.out / "indexed_script_private.json").write_text(
        json.dumps(extracted, indent=2) + "\n", encoding="utf-8")
    (args.out / "byte_statistics.json").write_text(
        json.dumps(statistics(extracted), indent=2) + "\n", encoding="utf-8")
    report = {
        "source_sha256": extracted["base_rom_sha256"],
        "roundtrip_sha256": hashlib.sha256(reconstruct(data, extracted)).hexdigest(),
        "byte_identical": True,
        "indexed_records": len(extracted["entries"]),
        "group_counts": extracted["group_counts"],
        "limitation": "No Japanese glyph mapping, script meaning, or insertion/expansion has been verified.",
    }
    (args.out / "identity_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(extracted['entries'])} records, {extracted['group_counts']} groups")
    print(f"PASS: exact source -> extracted records -> reconstructed ROM; SHA-256 {report['roundtrip_sha256']}")
    print(f"PRIVATE output: {args.out.resolve()} (contains game script bytes; DO NOT commit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
