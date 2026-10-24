#!/usr/bin/env python3
"""v1.9: approved Bank-6 in-place batch injector + metadata/capacity audit.

Works with v1.8 520-record private TSV; does NOT relocate bank-6 pointers,
compress text, infer unknown two-byte headers, or claim whole-game coverage.
All output must stay in ignored work/. Build is cumulative with verified v1.7.

Commands:
  python tools/script_pipeline_v19.py audit ORIGINAL.zip [TSV] --out work/v19/audit.json
  python tools/script_pipeline_v19.py build ORIGINAL.zip TSV --out work/v19
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

from analyze_rom import read_source
from english_codec_v15 import encode
import script_pipeline_v18 as v18

B6_RECORDS=479
BANK6_BEG=0x18010
BANK6_END=0x1c010
SIMPLE_HEADER=b'\x00\x00'


def classify(source:bytes, rows:list[dict])->dict:
    """Read only; never classifies nonzero record headers as text."""
    if hashlib.sha256(source).hexdigest()!=v18.SHA:
        raise ValueError('Wrong original Japanese ROM')
    if len(rows)!=520 or any(x['bank']!='6' for x in rows[:B6_RECORDS]):
        raise ValueError('Bad bank-6 inventory')
    counters=Counter(); group_counts={}
    for group in ('1','2','3','4'):
        subset=[r for r in rows[:B6_RECORDS] if r['group']==group]
        plain=sum(bytes.fromhex(r['raw_hex'])[:2]==SIMPLE_HEADER for r in subset)
        group_counts[group]={'records':len(subset),'simple_header':plain,'complex_header':len(subset)-plain}
    potential=0;exact=0;too_long=0;complex_header=0;invalid=0
    for row in rows[:B6_RECORDS]:
        raw=bytes.fromhex(row['raw_hex'])
        prefix=raw[:2]
        counters[prefix.hex().upper()]+=1
        if not row['english']:continue
        if prefix!=SIMPLE_HEADER:
            complex_header+=1;continue
        candidate=row['english'].replace('\\n','\n')
        try: payload=encode(candidate,maximum_lines=2,maximum_chars_per_line=20).data
        except ValueError:invalid+=1;continue
        potential+=1
        if len(payload)+2<=len(raw):exact+=1
        else:too_long+=1
    return dict(records=B6_RECORDS,simple_header=sum(k['simple_header'] for k in group_counts.values()),
        complex_header=sum(k['complex_header'] for k in group_counts.values()),
        groups=group_counts,most_common_headers=counters.most_common(20),
        candidates_simple_header=potential, candidates_fitting_original_allocation=exact,
        candidates_too_long=too_long,candidates_complex_header=complex_header,
        candidates_invalid_characters_or_width=invalid,
        data_begin='0x18812',data_end_exclusive='0x1C007',
        free_space_status='No verified bank-6 spare area; nonzero bytes follow the final indexed string',
        limitation='All values are source/metadata counts; not runtime-approved injection coverage.')


def patch_simple_bank6(source:bytes, baseline:bytes, rows:list[dict])->tuple[bytes,dict]:
    """Keep all original pointers and first two metadata bytes; only edit original record bodies.

    Requires exact original data from validated v1.8 inventory; never modifies
    string neighbors or overlaps. Explicit approval is required, even if
    imported external draft text happens to fit.
    """
    if hashlib.sha256(source).hexdigest()!=v18.SHA or len(source)!=len(baseline):
        raise ValueError('Source checksum or patched image length mismatch')
    if len(rows)!=520:raise ValueError('Complete v1.8 inventory required')
    edited=bytearray(baseline)
    changes=[]
    for row in rows[:B6_RECORDS]:
        if row['status']!='approved':continue
        ix=int(row['index'])
        at=int(row['text_at'],16)
        length=int(row['allocated'])
        old=source[at:at+length]
        if row['id']!=f'B6-{ix:03d}' or old.hex()!=row['raw_hex']:
            raise ValueError(f'Original record identity mismatch: {row["id"]}')
        if at<BANK6_BEG or at+length>BANK6_END or old[-1]!=0 or length<4:
            raise ValueError(f'Bank-6 record bounds/termination invalid: {row["id"]}')
        if old[:2]!=SIMPLE_HEADER:
            raise ValueError(f'{row["id"]}: complex two-byte metadata {old[:2].hex()} not yet classified')
        if not row['english']:
            raise ValueError(f'{row["id"]}: approved without English text')
        if baseline[at:at+length]!=old:
            raise AssertionError(f'{row["id"]}: baseline overlaps original Bank 6 records')
        payload=encode(row['english'].replace('\\n','\n'),maximum_lines=2,
                       maximum_chars_per_line=20).data
        used=2+len(payload)
        if used>length:
            raise ValueError(f'{row["id"]}: English needs {used} bytes including metadata, original allocation {length} (overflow {used-length})')
        edited[at:at+length]=old[:2]+payload+b'\x00'*(length-used)
        changes.append({'id':row['id'],'original_offset':f'0x{at:05X}',
                        'allocated':length,'encoded_with_header':used,'unused_padding':length-used})
    allowed=set()
    for row in rows[:B6_RECORDS]:
        if row['status']=='approved':
            at=int(row['text_at'],16)
            allowed.update(range(at,at+int(row['allocated'])))
    if any(i not in allowed for i,(x,y) in enumerate(zip(edited,baseline)) if x!=y):
        raise AssertionError('Modified bytes outside approved Bank 6 records')
    if edited[BANK6_BEG:0x18812]!=source[BANK6_BEG:0x18812]:
        raise AssertionError('Changed original Bank 6 pointer table or non-indexed data')
    if edited[0x1c007:BANK6_END]!=source[0x1c007:BANK6_END]:
        raise AssertionError('Changed original data after indexed records')
    return bytes(edited),dict(approved_simple_records=len(changes),in_place_changes=changes,
                              bank6_pointer_table_unchanged=True,
                              complex_header_records_patched=0,
                              larger_english_records_relocated=0)


def inject(source:bytes, rows:list[dict])->tuple[bytes,bytes,dict]:
    """Layer approved simple Bank 6 rows on the same cumulative v1.7/v1.8 baseline."""
    edited_rows=[dict(row) for row in rows]
    for row in edited_rows[:B6_RECORDS]:
        if row['status']=='approved':row['status']='draft'
    forward18,reverse18,stats18=v18.inject(source,edited_rows)
    baseline=v18.v16.apply_ips(source,forward18)
    result,bank6=patch_simple_bank6(source,baseline,rows)
    fwd=v18.diff_ips(source,result)
    reverse=v18.diff_ips(result,source)
    if v18.v16.apply_ips(source,fwd)!=result or v18.v16.apply_ips(result,reverse)!=source:
        raise AssertionError('Exact cumulative forward/rollback validation failed')
    report={**stats18,**{k:v for k,v in bank6.items() if k!='in_place_changes'},
            'in_place_changes':bank6['in_place_changes'],
            'patched_sha256':hashlib.sha256(result).hexdigest(),
            'cumulative_ips_bytes':len(fwd),
            'exact_rollback':True,'bank6_runtime_verified':False,
            'scope':'Approved simple-header Bank 6 records, Bank 8 approved events, v1.7 font/menu'}
    return fwd,reverse,report


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('audit');a.add_argument('source',type=Path)
    a.add_argument('tsv',nargs='?',type=Path);a.add_argument('--out',type=Path,default=Path('work/v19/audit.json'))
    b=sub.add_parser('build');b.add_argument('source',type=Path);b.add_argument('tsv',type=Path)
    b.add_argument('--out',type=Path,default=Path('work/v19'))
    ns=p.parse_args(argv)
    source=read_source(ns.source)
    rows=v18.load_edited(source,ns.tsv) if ns.tsv else v18.inventory(source)
    if ns.command=='audit':
        output=classify(source,rows)
        ns.out.parent.mkdir(parents=True,exist_ok=True)
        ns.out.write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
    else:
        forward,undo,output=inject(source,rows)
        ns.out.mkdir(parents=True,exist_ok=True)
        (ns.out/'Square_Tom_Sawyer_Bulk_Bank6_Inplace_v19.ips').write_bytes(forward)
        (ns.out/'Square_Tom_Sawyer_Bulk_Bank6_Inplace_v19_ROLLBACK_PRIVATE.ips').write_bytes(undo)
        (ns.out/'manifest.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
    print(json.dumps(output,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
