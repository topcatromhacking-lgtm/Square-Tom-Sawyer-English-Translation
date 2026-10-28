#!/usr/bin/env python3
"""v30 reversible four-line English pagination pilot, based on v27.

The user's v29 trace observed live 02/01 controls. The public translation
script's [BR][LN] matches the v27 English 02 01 sequence. This *does not*
establish whether 02 clears the window, waits for input, or both.

This deliberately NON-STORY diagnostic adds one 4th English line to the
accessible B6-356 dialogue using token F0 (index 33). It must be applied
alone to the exact original Japanese ROM, NOT stacked on the v27 IPS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

from analyze_rom import get_record_map, read_source
from english_codec_v15 import encode
import accessible_english_pilot_v27 as v27

SOURCE_SHA = v27.ORIGINAL_SHA
TABLE = v27.TABLE
TAIL_END = 0x1C007
FOURTH_TOKEN = 0xF0
FOURTH_PHRASE = "PAGE FOUR TEST."
FOUR_LINE_BODY = bytes.fromhex("EF 02 01 ED 01 EE 02 01 F0 00")
EXISTING = v27.PHRASES
ALL_PHRASES = EXISTING + ((FOURTH_TOKEN, FOURTH_PHRASE),)
OLD_PHRASE_BEGIN = TABLE + 2 * (1 + 29 + len(EXISTING))
NEW_PHRASE_BEGIN = TABLE + 2 * (1 + 29 + len(ALL_PHRASES))


def dictionary_body(text: str) -> bytes:
    return b"\x00\x00" + encode(
        text, maximum_lines=1, maximum_chars_per_line=20
    ).data


def extend_dictionary(base: bytes, *, tail_end: int = TAIL_END):
    """Pure bytes-only reallocation: keep the 29 original shared targets.

    Moves the three v27 phrases two bytes to make room for entry 33, then
    appends a diagnostic fourth phrase. No new decoder instructions.
    """
    if not (TABLE + 68 <= OLD_PHRASE_BEGIN + 2 and NEW_PHRASE_BEGIN == OLD_PHRASE_BEGIN + 2):
        raise AssertionError("Unexpected independent table layout")
    if len(base) < tail_end or tail_end > TAIL_END:
        raise ValueError("Invalid tail boundary")
    if base[OLD_PHRASE_BEGIN - 2:OLD_PHRASE_BEGIN] != struct.pack(
        "<H", v27.v26.cpu_of(OLD_PHRASE_BEGIN + sum(
            len(dictionary_body(t)) for _, t in EXISTING[:2]
        ))
    ):
        raise ValueError("v27 last dictionary pointer fingerprint changed")
    old_cursor = OLD_PHRASE_BEGIN
    for index, (token, phrase) in enumerate(EXISTING, 30):
        expected_ptr = v27.v26.cpu_of(old_cursor)
        actual_ptr = struct.unpack_from("<H", base, TABLE + 2 * index)[0]
        blob = dictionary_body(phrase)
        if token != 0xCF + index or actual_ptr != expected_ptr:
            raise ValueError("Previous English token table changed")
        if base[old_cursor:old_cursor + len(blob)] != blob:
            raise ValueError("Previous v27 English phrase bytes changed")
        old_cursor += len(blob)
    if base[old_cursor:tail_end] != bytes(tail_end - old_cursor):
        raise ValueError("Expected clean old Bank6 dictionary tail")
    result = bytearray(base)
    result[OLD_PHRASE_BEGIN:tail_end] = bytes(tail_end - OLD_PHRASE_BEGIN)
    cursor = NEW_PHRASE_BEGIN
    phrases = []
    for index, (token, phrase) in enumerate(ALL_PHRASES, 30):
        if token != 0xCF + index:
            raise AssertionError("Token index must match fixed $CF decoder offset")
        blob = dictionary_body(phrase)
        if cursor + len(blob) > tail_end:
            raise ValueError("No room for fourth English dictionary phrase")
        struct.pack_into("<H", result, TABLE + 2 * index,
                         v27.v26.cpu_of(cursor))
        result[cursor:cursor + len(blob)] = blob
        phrases.append({"token": f"{token:02X}", "index": index,
                        "cpu_pointer": f"{v27.v26.cpu_of(cursor):04X}",
                        "english": phrase, "bytes": len(blob)})
        cursor += len(blob)
    if result[TABLE:TABLE + 60] != base[TABLE:TABLE + 60]:
        raise AssertionError("Original 29 shared pointers or sentinel modified")
    return bytes(result), {"dictionary_end_file": f"{cursor:05X}",
                            "free_tail_bytes": tail_end - cursor,
                            "tokens": phrases, "preserved_native_targets": 29}


def build(original: bytes):
    if len(original) != 262160 or hashlib.sha256(original).hexdigest() != SOURCE_SHA:
        raise ValueError("Expected exact Japanese ROM source SHA-256")
    fw_v27, _, v27_report = v27.build(original)
    baseline = v27.v23.v16.apply_ips(original, fw_v27)
    records, _ = get_record_map(original)
    start, stop, old = v27.record_slice(baseline, records, v27.TARGET)
    expected_old = b"\x00\x00" + v27.NEW_BODY
    if old[:len(expected_old)] != expected_old or any(old[len(expected_old):]):
        raise ValueError("v27 record B6-356 changed")
    if len(old) < 2 + len(FOUR_LINE_BODY):
        raise ValueError("Cannot fit four-line pilot into record allocation")

    rebuilt, dict_report = extend_dictionary(baseline)
    out = bytearray(rebuilt)
    out[start:stop] = old[:2] + FOUR_LINE_BODY + bytes(
        len(old) - 2 - len(FOUR_LINE_BODY)
    )

    for rec in records:
        at = int(rec["table_file_offset"], 16)
        if out[at:at + 2] != baseline[at:at + 2]:
            raise AssertionError("Main Bank6 pointer unexpectedly changed")
    if out[0x2124D:0x213EC] != baseline[0x2124D:0x213EC]:
        raise AssertionError("Previously verified opening changed")
    if out[0x3D1AF:0x3D1CB] != baseline[0x3D1AF:0x3D1CB]:
        raise AssertionError("Previously verified menu changed")
    if out[:16] != original[:16] or len(out) != len(original):
        raise AssertionError("Mapper/header or ROM size changed")
    allowed = set(range(start, stop)) | set(range(TABLE + 60, TAIL_END))
    unexpected = {i for i, (a, b) in enumerate(zip(baseline, out))
                  if a != b and i not in allowed}
    if unexpected:
        raise AssertionError(f"Unexpected ROM changes: {sorted(unexpected)[:10]}")
    completed = bytes(out)
    forward = v27.v18.diff_ips(original, completed)
    reverse = v27.v18.diff_ips(completed, original)
    apply = v27.v23.v16.apply_ips
    if apply(original, forward) != completed or apply(completed, reverse) != original:
        raise AssertionError("Cumulative IPS/byte-exact rollback failed")
    info = {
        "version": "v30-four-line-English-pagination-pilot",
        "source_sha256": SOURCE_SHA,
        "v27_sha256": v27_report["patched_sha256"],
        "patched_sha256": hashlib.sha256(completed).hexdigest(),
        "forward_ips_sha256": hashlib.sha256(forward).hexdigest(),
        "exact_rollback": True,
        "source_dialogue": "B6-356",
        "source_visitor": "existing nearby LOOK/NPC interaction",
        "pilot_text": ["THE ANGEL WHISPERED.", "THERE'S NOTHING",
                       "FOR YOU HERE.", FOURTH_PHRASE],
        "diagnostic_not_story_accurate": True,
        "runtime_page_semantics_verified": False,
        "new_token": "F0",
        "new_primary_body_hex": FOUR_LINE_BODY.hex(),
        "primary_game_dialogue_pointer_edits_vs_v27": 0,
        "dictionary": dict_report,
        "requires_fceux": True,
        "note": "Standalone IPS from clean original only; do not stack v27."
    }
    return forward, reverse, info


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("--out", type=Path, default=Path("work/v30"))
    args = parser.parse_args(argv)
    forward, reverse, report = build(read_source(args.original))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "Square_Tom_Sawyer_v30_FourLine_Pagination_DIAGNOSTIC.ips").write_bytes(forward)
    (args.out / "Square_Tom_Sawyer_v30_ROLLBACK_PRIVATE.ips").write_bytes(reverse)
    (args.out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n",
                                             encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
