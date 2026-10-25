#!/usr/bin/env python3
"""v22 experimental native $03 indirection on an exact duplicate literal.

Purpose: a reversible decoder smoke test without modifying 6502 routines,
PRG mapper mode, original pointers, 29 shared phrases or dialogue allocations.
This is NOT new one-byte dictionary compression or a full English translation.

The default patch replaces one complete four-byte original literal in B6-420
with $03,$01, leaving its allocation fixed (trailing zeros padded), and builds
on the already FCEUX-tested cumulative v1.7 English intro/menu.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from analyze_rom import read_source,get_record_map
import build_opening_v16 as v16
import build_overworld_menu_v17 as v17

SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
INDEX_TO_PROBE=420
REF_INDEX=1

def record_bytes(original:bytes,recs:list[dict],index:int)->tuple[int,bytes]:
    r=recs[index];pos=int(r['text_file_offset'],16)
    return pos,original[pos:pos+r['length_bytes']]

def expand_native(raw:bytes,targets:list[bytes])->bytes:
    """Single-level logical stream expander, not a simulation of display timing.

    The validated smoke record has no complex controls. It starts with two
    metadata bytes; every $03,index pair references a target with a two-byte
    prefix and one 00 terminator. Returns expanded body only, without ending 00.
    """
    if len(raw)<3 or 0 not in raw[2:]:
        raise ValueError('Invalid source record termination')
    stop=raw.index(0,2)
    if any(raw[stop:]):
        raise ValueError('Invalid source record termination: nonzero data after terminator')
    result=bytearray();i=2
    while i<stop:
        c=raw[i]
        if c!=3:result.append(c);i+=1;continue
        if i+1>=stop:raise ValueError('Truncated native reference index')
        index=raw[i+1]
        if not 1<=index<=len(targets):raise ValueError('Unknown reference')
        phrase=targets[index-1]
        if phrase[-1]!=0 or 3 in phrase[2:-1] or b'\x00' in phrase[2:-1]:
            raise ValueError('Recursive or malformed native reference')
        result.extend(phrase[2:-1]);i+=2
    return bytes(result)

def eligible_duplicate_literals(original:bytes)->list[dict]:
    """Find exact opportunities without nested references or control codes.

    Restrict to records 29..478, original simple 00-00 metadata and bodies
    without byte values 1..8. This is intentionally conservative.
    """
    records,_=get_record_map(original)
    phrases=[record_bytes(original,records,i)[1] for i in range(29)]
    results=[]
    for ix in range(29,len(records)):
        at,raw=record_bytes(original,records,ix)
        if raw[:2]!=b'\x00\x00' or any(x<=8 for x in raw[2:-1]):continue
        body=raw[2:-1]
        for ti,p in enumerate(phrases,1):
            phrase=p[2:-1]
            if len(phrase)<3 or any(x<=8 for x in phrase):continue
            offset=body.find(phrase)
            if offset>=0:
                results.append({'record':ix,'reference_index':ti,
                    'literal_offset_in_body':offset,'length':len(phrase),
                    'potential_savings_bytes':len(phrase)-2})
    return results

def build(original:bytes)->tuple[bytes,bytes,dict]:
    if len(original)!=262160 or hashlib.sha256(original).hexdigest()!=SHA:
        raise ValueError('Exact unmodified Japanese original required')
    records,summary=get_record_map(original)
    if len(records)!=479:raise ValueError('Record count drift')
    at,raw=record_bytes(original,records,INDEX_TO_PROBE)
    phrase_at,phrase=record_bytes(original,records,REF_INDEX-1)
    if raw[:2]!=b'\x00\x00' or raw[2:-1]!=phrase[2:-1] or len(raw)!=7 or len(phrase)!=7:
        raise ValueError('Source reference/target structure changed')
    if 3 in phrase[2:-1] or not all(x>8 for x in phrase[2:-1]):
        raise ValueError('Unexpected nested or control-bearing target')
    replacement=raw[:2]+bytes([3,REF_INDEX,0])+bytes(len(raw)-5)
    original_target=[record_bytes(original,records,i)[1] for i in range(29)]
    if expand_native(replacement,original_target)!=expand_native(raw,original_target):
        raise AssertionError('Native reference does not reproduce original literal')
    baseline_fw,_,report17=v17.build(original)
    known_good=v16.apply_ips(original,baseline_fw)
    if known_good[at:at+len(raw)]!=raw:
        raise ValueError('Existing v1.7 changes overlap chosen record')
    modified=bytearray(known_good)
    modified[at:at+len(raw)]=replacement
    if modified[:16]!=original[:16] or len(modified)!=len(original):
        raise AssertionError('Bad ROM structure')
    edits={k for k,(a,b) in enumerate(zip(known_good,modified)) if a!=b}
    if not edits or not edits.issubset(set(range(at,at+len(raw)))):
        raise AssertionError('Changes escape smoke record')
    if modified[0x18010:0x18812]!=original[0x18010:0x18812]:
        raise AssertionError('Changed Bank 6 pointer/delimiter/table space')
    fwd=v16.make_ips(v17.parse_ips(baseline_fw)+[(at,replacement)])
    back=v16.make_ips([(a,bytes(original[a:a+len(blob)])) for a,blob in v17.parse_ips(baseline_fw)]+[(at,raw)])
    if v16.apply_ips(original,fwd)!=modified or v16.apply_ips(modified,back)!=original:
        raise AssertionError('Cumulative IPS or exact reverse mismatch')
    manifest={'version':'v22-native-ref-smoke','source_sha256':SHA,
        'cumulative_baseline':'v1.7 English intro/menu','baseline_sha256':report17['patched_sha256'],
        'patched_sha256':hashlib.sha256(modified).hexdigest(),
        'forward_ips_sha256':hashlib.sha256(fwd).hexdigest(),
        'rollback_exact':True,'reference_control':'03 01',
        'selected_bank6_record':'B6-420','record_file_offset':f'0x{at:05X}',
        'reference_target':'B6-000','original_indexed_pointers_changed':0,
        'baseline_additional_changed_bytes':len(edits),'logical_stream_equal_original':True,
        'allocated_bytes_saved':0,'reclaimable_in_full_repack_bytes':len(phrase[2:-1])-2,
        'fceux_runtime_verified':False,
        'limitation':'Uses existing 2-byte native reference, not a new 1-byte token decoder. Placement/naming of target record in gameplay still needs runtime confirmation.'}
    return fwd,back,manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original',type=Path)
    p.add_argument('--out',type=Path,default=Path('work/v22'))
    args=p.parse_args();data=read_source(args.original)
    fw,rv,manifest=build(data)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'Square_Tom_Sawyer_v22_Native_Reference_SMOKE.ips').write_bytes(fw)
    (args.out/'Square_Tom_Sawyer_v22_Native_Reference_ROLLBACK_PRIVATE.ips').write_bytes(rv)
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
