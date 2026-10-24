#!/usr/bin/env python3
"""Create a private, pointer-verified Square no Tom Sawyer script capacity inventory.

Reads a SHA-gated Japanese ROM and optional locally obtained BlackPaladin script
files. Never writes a patched ROM. Script/translation output stays in ignored
work/, never in Git. Candidate lengths are LOWER BOUNDS, not encoded sizes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from analyze_rom import get_record_map, read_source

SHA256 = 'ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
PTR_RE = re.compile(r'^//POINTER #(\d+) @ \$([0-9A-Fa-f]+) - STRING #(\d+) @ \$([0-9A-Fa-f]+)', re.M)
END_RE = re.compile(r'\[ED\]', re.I)


def extract_candidates(script_text: str, source_name: str) -> list[dict]:
    """Extract candidate English, retaining mismatched refs for review."""
    matches = list(PTR_RE.finditer(script_text))
    entries = []
    for i, match in enumerate(matches):
        section = script_text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(script_text)]
        pointer = int(match.group(2), 16)
        string_at = int(match.group(4), 16)
        end = END_RE.search(section)
        if end:
            translation = ' '.join(line.strip() for line in section[end.end():].splitlines() if line.strip())
            # Manual uncertainty markers are not candidate translations.
            if translation.startswith('^(('):
                translation = ''
        else:
            translation = ''
        entries.append({
            'script_file': source_name,
            'external_index': int(match.group(1)),
            'pointer_file_offset': pointer,
            'text_file_offset': string_at,
            'english_candidate': translation,
            'end_marker_seen': bool(end),
        })
    return entries


def lower_bound_bytes(english: str) -> int | None:
    """At least one byte per visible character plus a terminating 00.

    This is NOT a valid English encoding or a screen-width calculation.
    A real encoder must support any punctuation, accents, controls, and names.
    """
    if not english:
        return None
    return len(english) + 1


def reconcile(records: list[dict], candidates: list[dict]) -> tuple[list[dict], list[dict], dict]:
    by_pointer: dict[int, list[dict]] = {}
    for item in candidates:
        by_pointer.setdefault(item['pointer_file_offset'], []).append(item)
    rows = []
    matched_ids = set()
    for rec in records:
        ptr = int(rec['table_file_offset'], 16)
        text = int(rec['text_file_offset'], 16)
        options = by_pointer.get(ptr, [])
        exact = [c for c in options if c['text_file_offset'] == text]
        if len(exact) == 1:
            candidate = exact[0]
            matched_ids.add(id(candidate))
            english = candidate['english_candidate']
            status = 'MATCHED' if english else 'MATCHED_NO_USABLE_TRANSLATION'
            source = candidate['script_file']
        else:
            english = ''
            source = ''
            status = 'DUPLICATE_REFERENCE' if len(exact) > 1 else 'OFFSET_MISMATCH' if options else 'NOT_IN_EXTERNAL_SCRIPT'
        size = rec['length_bytes']
        req = lower_bound_bytes(english)
        rows.append({
            'global_index':rec['global_index'],
            'group':rec['group'],
            'pointer_file_offset':rec['table_file_offset'],
            'cpu_pointer':rec['cpu_pointer'],
            'text_file_offset':rec['text_file_offset'],
            'allocated_bytes':size,
            'max_payload_bytes':size-1,
            'source_script':source,
            'match_status':status,
            'english_candidate':english,
            'candidate_characters':len(english),
            'minimum_one_byte_requirement':req if req is not None else '',
            'minimum_overflow_bytes':max(0,req-size) if req is not None else '',
            'requires_encoding_review':bool(english and any(not 0x20 <= ord(c) <= 0x7E for c in english)),
            'requires_control_and_width_review':bool(english),
        })
    extras=[]
    for c in candidates:
        if id(c) in matched_ids: continue
        p=c['pointer_file_offset']
        why='GROUP_DELIMITER_FFFF' if p in (0x1820A,0x18252) else (
            'DUPLICATE_REFERENCE' if len(by_pointer[p])>1 else
            'UNMATCHED_POINTER_OR_STRING_OFFSET')
        extras.append({**c,'reason':why})
    summary={
        'source_rom_sha256':SHA256,
        'validated_rom_records':len(rows),
        'external_script_entries':len(candidates),
        'exact_matches':sum(r['match_status'] in ('MATCHED','MATCHED_NO_USABLE_TRANSLATION') for r in rows),
        'entries_with_candidate':sum(bool(r['english_candidate']) for r in rows),
        'minimum_length_overflows':sum(isinstance(r['minimum_overflow_bytes'],int) and r['minimum_overflow_bytes']>0 for r in rows),
        'unmatched_external_entries':len(extras),
        'group_delimiter_entries':sum(c['reason']=='GROUP_DELIMITER_FFFF' for c in extras),
        'missing_or_mismatched_rom_records':sum(r['match_status'] not in ('MATCHED','MATCHED_NO_USABLE_TRANSLATION') for r in rows),
        'scope':'Only 479 bank-6 indexed entries; other banks require separate inventory.',
        'caution':'Minimum length assumes one byte per visible character plus terminator; not an executable translation or a verified encoding.',
    }
    return rows, extras, summary


def write_tsv(path: Path, rows: list[dict], keys: list[str]) -> None:
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,delimiter='\t',extrasaction='ignore')
        w.writeheader();w.writerows(rows)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path,help='exact Japanese NES ROM or ZIP')
    p.add_argument('--script',action='append',type=Path,default=[],help='local BlackPaladin script text file, repeatable')
    p.add_argument('--out',type=Path,default=Path('work/v14'))
    args=p.parse_args()
    source=read_source(args.rom)
    if hashlib.sha256(source).hexdigest()!=SHA256:raise ValueError('ROM SHA-256 mismatch')
    records,source_summary=get_record_map(source)
    candidates=[]
    for path in args.script:
        candidates+=extract_candidates(path.read_text(encoding='utf-8-sig'),path.name)
    rows,unmatched,summary=reconcile(records,candidates)
    if len(rows)!=479:raise AssertionError('Validated source count changed')
    # Store potential copyrighted third-party text only in the local ignored output.
    args.out.mkdir(parents=True,exist_ok=True)
    write_tsv(args.out/'master_script_PRIVATE.tsv',rows,list(rows[0]))
    if unmatched:write_tsv(args.out/'unmatched_references_PRIVATE.tsv',unmatched,list(unmatched[0]))
    (args.out/'summary.json').write_text(json.dumps({**summary,'group_counts':source_summary['group_counts']},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print('Private records saved to:',args.out)
    return 0

if __name__=='__main__':raise SystemExit(main())
