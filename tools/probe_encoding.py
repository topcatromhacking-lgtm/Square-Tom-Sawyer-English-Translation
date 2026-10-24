#!/usr/bin/env python3
"""Static encoded-text and CHR-tile probe for Square no Tom Sawyer (Famicom).

No guessed Japanese mappings. Inventories recurring structural patterns,
exports 8x8 two-bitplane tiles from a candidate PRG bank, and writes only
statistics/ROM offsets in JSON. Original game bytes stay in the private PNG.
No emulator or renderer/text-to-glyph mapping is claimed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import json
import math
import struct
import zlib

from analyze_rom import read_source, get_record_map

BANK_SIZE = 0x4000
HEADER_SIZE = 16


def text_patterns(data: bytes, records: list[dict]) -> dict:
    blocks = []
    for rec in records:
        at = int(rec["text_file_offset"], 16)
        blocks.append(data[at:at + rec["length_bytes"]])
    counts = Counter(b for block in blocks for b in block)
    pos = [Counter(block[i] for block in blocks if len(block) > i) for i in range(4)]
    ends = Counter(block[-2] for block in blocks if len(block) >= 2)
    pairs = Counter()
    triples = Counter()
    for block in blocks:
        pairs.update(zip(block, block[1:]))
        triples.update(zip(block, block[1:], block[2:]))

    def most(c, n=16):
        return [{"hex": bytes(k).hex().upper() if isinstance(k, tuple) else f"{k:02X}",
                 "count": v} for k, v in c.most_common(n)]

    return {
        "record_count": len(blocks),
        "total_bytes": sum(map(len, blocks)),
        "unique_byte_values": len(counts),
        "most_common_bytes": most(counts),
        "common_at_absolute_positions_0_to_3": [most(c, 8) for c in pos],
        "common_before_terminator": most(ends, 12),
        "common_adjacent_byte_pairs": most(pairs, 12),
        "common_adjacent_byte_triples": most(triples, 12),
        "terminator_00_at_end_of_all_records": all(b and b[-1] == 0 for b in blocks),
        "count_of_22_at_position_2": sum(len(b) > 2 and b[2] == 0x22 for b in blocks),
        "caution": "Frequent bytes have NOT been assigned rendering/control meanings.",
    }


def tile_pixels(data: bytes, bank: int, tile: int) -> list[int]:
    if not (0 <= bank <= 15 and 0 <= tile < 1024):
        raise ValueError("Invalid PRG bank/tile index")
    pos = HEADER_SIZE + bank * BANK_SIZE + tile * 16
    raw = data[pos:pos + 16]
    if len(raw) != 16:
        raise ValueError("Tile extends outside ROM")
    pixels = []
    for y in range(8):
        lo, hi = raw[y], raw[y + 8]
        for x in range(8):
            shift = 7 - x
            pixels.append(((lo >> shift) & 1) | (((hi >> shift) & 1) << 1))
    return pixels


def _chunk(name: bytes, value: bytes) -> bytes:
    blob = name + value
    return struct.pack(">I", len(value)) + blob + struct.pack(">I", zlib.crc32(blob))


def png_rgb(width: int, height: int, rgb: bytes) -> bytes:
    if len(rgb) != width * height * 3 or not width or not height:
        raise ValueError("Invalid RGB image")
    scan = b"".join(b"\0" + rgb[y*width*3:(y+1)*width*3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(scan, 9))
            + _chunk(b"IEND", b""))


def atlas(data: bytes, bank: int = 8, first: int = 224, count: int = 96,
          columns: int = 16, scale: int = 4) -> tuple[bytes, dict]:
    if not (0 <= first < 1024 and 1 <= count <= 1024 - first and
            1 <= columns <= 64 and 1 <= scale <= 12):
        raise ValueError("Invalid atlas layout")
    rows = math.ceil(count / columns)
    width, height = columns*8*scale, rows*8*scale
    output = bytearray([255] * (width*height*3))
    tones = (255, 164, 82, 0)
    mapping = []
    for j in range(count):
        tile = first + j
        x0, y0 = (j % columns)*8*scale, (j // columns)*8*scale
        pixels = tile_pixels(data, bank, tile)
        for y in range(8):
            for x in range(8):
                gray = tones[pixels[y*8+x]]
                for dy in range(scale):
                    for dx in range(scale):
                        at = ((y0+y*scale+dy)*width+x0+x*scale+dx)*3
                        output[at:at+3] = bytes((gray, gray, gray))
        mapping.append({
            "tile_index": tile,
            "rom_file_offset": f"0x{HEADER_SIZE + bank*BANK_SIZE + tile*16:05X}",
            "image_column": j % columns, "image_row": j // columns,
        })
    meta = {
        "bank_zero_based": bank, "first_tile": first, "tile_count": count,
        "columns": columns, "scale": scale, "tile_size_bytes": 16,
        "format": "NES 2-bitplane 8x8; candidate graphics, NOT verified renderer glyphs",
        "tiles": mapping,
    }
    return png_rgb(width, height, output), meta


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path, help="Verified original .nes or .zip")
    p.add_argument("--out", type=Path, default=Path("work/font-probe"))
    p.add_argument("--bank", type=int, default=8)
    p.add_argument("--first-tile", type=int, default=224)
    p.add_argument("--count", type=int, default=96)
    args = p.parse_args(argv)
    data = read_source(args.source)
    records, _ = get_record_map(data)
    report = text_patterns(data, records)
    png, info = atlas(data, args.bank, args.first_tile, args.count)
    args.out.mkdir(exist_ok=True, parents=True)
    (args.out / "encoded_text_patterns.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf8")
    (args.out / "tile_atlas_map.json").write_text(json.dumps(info, indent=2)+"\n", encoding="utf8")
    (args.out / "candidate_tiles.png").write_bytes(png)
    print(f"PASS: {len(records)} original record boundaries verified")
    print(f"Candidate atlas: PRG bank {args.bank}, tiles {args.first_tile}..{args.first_tile+args.count-1}")
    print("PROVISIONAL: no text byte-to-glyph mapping or runtime renderer proven")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
