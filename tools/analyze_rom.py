#!/usr/bin/env python3
"""Read-only Square no Tom Sawyer (Famicom) ROM inventory.

Accepts an original .nes file or a ZIP containing exactly one .nes.
Never modifies or copies the original ROM. Default reports contain
no game text bytes; --private-hex adds bytes to ignored LOCAL work files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import struct
import zipfile
import zlib

EXPECTED_SHA1 = "f00d2feb353450bd6294bb431a54cee729e56689"
EXPECTED_CRC32 = "AEA5B066"
EXPECTED_SIZE = 262160
ROM_BANK_START = 0x18010
TABLE_END = 0x18412
BANK_SIZE = 0x4000


def read_source(path: pathlib.Path) -> bytes:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            entries = [e for e in z.infolist()
                       if not e.is_dir() and e.filename.lower().endswith(".nes")]
            if len(entries) != 1:
                raise ValueError(f"Expected exactly one .nes entry, found {len(entries)}")
            return z.read(entries[0])
    if path.suffix.lower() == ".nes":
        return path.read_bytes()
    raise ValueError("Input must be a .nes or .zip containing one .nes")


def identity(data: bytes) -> dict:
    if len(data) < 16 or data[:4] != b"NES\x1a":
        raise ValueError("Not an iNES ROM")
    header = data[:16]
    mapper = (header[6] >> 4) | (header[7] & 0xF0)
    trainer_size = 512 if header[6] & 0x04 else 0
    claimed_size = 16 + trainer_size + header[4] * BANK_SIZE + header[5] * 8192
    report = {
        "rom_size_bytes": len(data),
        "crc32": f"{zlib.crc32(data) & 0xffffffff:08X}",
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "ines_header_hex": header.hex(),
        "ines_version": 2 if header[7] & 0x0C == 0x08 else 1,
        "prg_rom_bytes": header[4] * BANK_SIZE,
        "chr_rom_bytes": header[5] * 8192,
        "prg_banks_16k": header[4],
        "mapper": mapper,
        "battery_ram_flag": bool(header[6] & 0x02),
        "trainer_flag": bool(header[6] & 0x04),
        "header_reported_image_size": claimed_size,
    }
    if claimed_size != len(data):
        raise ValueError("ROM length does not match iNES header")
    return report


def get_record_map(data: bytes) -> tuple[list[dict], dict]:
    meta = identity(data)
    if (meta["sha1"] != EXPECTED_SHA1 or
            meta["rom_size_bytes"] != EXPECTED_SIZE or
            meta["crc32"] != EXPECTED_CRC32):
        raise ValueError("Wrong base ROM. No extraction performed; verify SHA-1/CRC32 and header")

    end_ptr = struct.unpack_from("<H", data, ROM_BANK_START)[0]
    if end_ptr != 0xBFF7:
        raise ValueError(f"Unexpected text end pointer: {end_ptr:#06x}")

    words = [(at, struct.unpack_from("<H", data, at)[0])
             for at in range(ROM_BANK_START + 2, TABLE_END, 2)]
    if words[0][1] != 0xFFFF or words[-1][1] != 0xFFFF:
        raise ValueError("Unexpected dialogue table boundary markers")

    # A $FFFF delimiter ends each non-empty group; additional padding is ignored.
    groups = []
    group = []
    for at, ptr in words:
        if ptr == 0xFFFF:
            if group:
                groups.append(group)
                group = []
        else:
            if not 0x8000 <= ptr < 0xC000:
                raise ValueError(f"Unexpected table entry at {at:#x}: {ptr:#x}")
            group.append((at, ptr))
    if group:
        groups.append(group)

    entries = [(group_number, group_index, at, ptr)
               for group_number, group in enumerate(groups, 1)
               for group_index, (at, ptr) in enumerate(group)]
    ptrs = [r[3] for r in entries]
    if not ptrs:
        raise ValueError("No indexed text records")
    if len(ptrs) != len(set(ptrs)) or ptrs != sorted(ptrs):
        raise ValueError("Pointer ordering or uniqueness error")

    lengths = [next_ptr - ptr for ptr, next_ptr in
               zip(ptrs, ptrs[1:] + [end_ptr])]
    records = []
    for number, ((group_number, group_index, ptr_at, ptr), length) in enumerate(zip(entries, lengths)):
        if length <= 0:
            raise ValueError(f"Negative or zero record length at #{number}")
        at = ROM_BANK_START + ptr - 0x8000
        raw = data[at:at + length]
        if len(raw) != length or raw[-1] != 0:
            raise ValueError(f"Record #{number} has invalid offset/terminator")
        records.append({
            "global_index": number,
            "group": group_number,
            "index_in_group": group_index,
            "table_file_offset": f"0x{ptr_at:05X}",
            "cpu_pointer": f"0x{ptr:04X}",
            "text_file_offset": f"0x{at:05X}",
            "length_bytes": length,
            "terminator": "0x00",
        })

    summary = {
        "base_rom_sha1": meta["sha1"],
        "mapper": meta["mapper"],
        "prg_banks_16k": meta["prg_banks_16k"],
        "dialogue_prg_bank_zero_based": (ROM_BANK_START - 16) // BANK_SIZE,
        "end_pointer_file_offset": f"0x{ROM_BANK_START:05X}",
        "end_cpu_pointer": f"0x{end_ptr:04X}",
        "pointer_table_file_span": ["0x18010", "0x18411"],
        "text_start_file_offset": records[0]["text_file_offset"],
        "text_end_file_offset_exclusive": f"0x{ROM_BANK_START + end_ptr - 0x8000:05X}",
        "records": len(records),
        "groups": len(groups),
        "group_counts": [len(g) for g in groups],
        "text_span_bytes": sum(lengths),
        "shortest_record_bytes": min(lengths),
        "longest_record_bytes": max(lengths),
        "every_record_zero_terminated": True,
        "all_records_are_unique_and_ordered": True,
        "scope": "Indexed candidate dialogue bank only; NOT every Japanese/graphics/menu string.",
    }
    return records, summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=pathlib.Path, help="Original .nes or ZIP")
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("work/recon"))
    parser.add_argument("--private-hex", action="store_true",
                        help="Also emit encoded game text bytes; keep private and out of Git")
    args = parser.parse_args(argv)

    data = read_source(args.source)
    records, summary = get_record_map(data)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "identity.json").write_text(
        json.dumps(identity(data), indent=2) + "\n", encoding="utf-8")
    (args.out / "dialogue_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    columns = list(records[0]) + (["raw_hex"] if args.private_hex else [])
    with (args.out / "pointer_inventory.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in records:
            row = record.copy()
            if args.private_hex:
                at = int(record["text_file_offset"], 16)
                row["raw_hex"] = data[at:at + record["length_bytes"]].hex()
            writer.writerow(row)

    print(f"ROM verified (SHA-1 {identity(data)['sha1']}); "
          f"{len(records)} indexed records in {summary['group_counts']} groups")
    print(f"Reports written to {args.out.resolve()}")
    if args.private_hex:
        print("PRIVATE HEX ENABLED: never commit the generated CSV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
