#!/usr/bin/env python3
"""v23: experimentally re-encode existing 29 $03 references as 1-byte tokens.

TOKEN D0..EC => original shared entry indices 1..29. Uses a 13-byte edit
of the original existing 6502 interpreter code, NOT any injected code cave.
Rewrites all 237 original indexed $03,index references atomically, and repacks
479 records in the original Bank6 allocation with source-verified pointers.

Runtime still unverified: any unindexed source use of $03 is a residual risk.
This is a cumulative v1.7 + experimental-native-token standalone IPS.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from analyze_rom import read_source,get_record_map
import build_overworld_menu_v17 as v17
import build_opening_v16 as v16
import script_pipeline_v18 as v18

SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
FIRST_TOKEN=0xD0
LAST_TOKEN=0xEC
DISPATCH_CPU=0xEDE7
RESOLVER_CPU=0xEDFD
NEW_DISPATCH=bytes.fromhex('C9 D0 90 06')
NEW_RESOLVER=bytes.fromhex('38 E9 CF 85 F1 A9 00 85 F2')
ORIG_DISPATCH=bytes.fromhex('C9 03 D0 06')
ORIG_RESOLVER=bytes.fromhex('A9 00 85 F2 20 92 ED 85 F1')
FIRST_TEXT=0x18812
END_TEXT=0x1C007
BANK6_START=0x18010
FIXED_START=0x3C010

def at_cpu(pc):return FIXED_START+pc-0xC000

def original_raw(rom,records):
    return [rom[int(r['text_file_offset'],16):int(r['text_file_offset'],16)+r['length_bytes']] for r in records]

def converted_body(raw:bytes)->tuple[bytes,int]:
    if len(raw)<3 or raw[-1]!=0 or 0 in raw[2:-1]:raise ValueError('Invalid indexed record termination')
    body=raw[2:-1];out=bytearray();i=0;refs=0
    while i<len(body):
        code=body[i]
        if code>=FIRST_TOKEN:
            raise ValueError(f'Preexisting raw body byte {code:02X} collides with token namespace')
        if code==3:
            if i+1>=len(body):raise ValueError('Incomplete native reference')
            index=body[i+1]
            if not 1<=index<=29:raise ValueError('Reference index not in shared phrase pool')
            out.append(FIRST_TOKEN+index-1);refs+=1;i+=2
        else:out.append(code);i+=1
    return raw[:2]+bytes(out)+b'\x00',refs

def expand_body(raw:bytes,targets:list[bytes],*,new_mode:bool)->bytes:
    body=raw[2:-1];out=bytearray();i=0
    while i<len(body):
        code=body[i]
        if new_mode and FIRST_TOKEN<=code<=LAST_TOKEN:
            idx=code-FIRST_TOKEN+1;fragment=targets[idx-1][2:-1]
            if 3 in fragment or any(b>=FIRST_TOKEN for b in fragment):raise ValueError('Nested target in new codec')
            out+=fragment;i+=1
        elif not new_mode and code==3:
            if i+1>=len(body):raise ValueError('Broken native ref')
            index=body[i+1]
            if not 1<=index<=29:raise ValueError('Invalid original reference')
            fragment=targets[index-1][2:-1]
            if 3 in fragment:raise ValueError('Nested source reference')
            out+=fragment;i+=2
        else:
            if new_mode and code==3:raise ValueError('Old two-byte native reference survived')
            out.append(code);i+=1
    return bytes(out)

def build(source:bytes)->tuple[bytes,bytes,dict]:
    if len(source)!=262160 or hashlib.sha256(source).hexdigest()!=SHA:
        raise ValueError('Exact source ROM required')
    records,metadata=get_record_map(source)
    if len(records)!=479 or metadata['group_counts']!=[251,35,123,70]:
        raise ValueError('Pointer corpus changed')
    if source[at_cpu(DISPATCH_CPU):at_cpu(DISPATCH_CPU)+4]!=ORIG_DISPATCH:
        raise ValueError('Original dispatcher bytes changed')
    if source[at_cpu(RESOLVER_CPU):at_cpu(RESOLVER_CPU)+9]!=ORIG_RESOLVER:
        raise ValueError('Original reference resolver bytes changed')
    words={int(r['table_file_offset'],16) for r in records}
    original=original_raw(source,records)
    translated=[];counts=[]
    for raw in original:
        current,n=converted_body(raw)
        translated.append(current);counts.append(n)
    if sum(counts)!=237 or len({i for raw in original for i in []})!=0:
        raise ValueError('Original native reference count drift')
    if any(counts[:29]):raise ValueError('Dictionary source unexpectedly nested')
    for idx,(before,after) in enumerate(zip(original,translated)):
        if before[:2]!=after[:2] or expand_body(before,original[:29],new_mode=False)!=expand_body(after,translated[:29],new_mode=True):
            raise AssertionError(f'Semantic expansion mismatch at B6-{idx:03d}')
    total=sum(map(len,translated));capacity=END_TEXT-FIRST_TEXT
    if total>capacity:raise ValueError('New data exceeds Bank 6')
    assert total==capacity-237
    baseline_fw,_,r17=v17.build(source)
    baseline=v16.apply_ips(source,baseline_fw)
    if baseline[0x18010:END_TEXT]!=source[0x18010:END_TEXT]:
        raise ValueError('Cumulative baseline already changes Bank 6')
    patched=bytearray(baseline)
    patched[at_cpu(DISPATCH_CPU):at_cpu(DISPATCH_CPU)+4]=NEW_DISPATCH
    patched[at_cpu(RESOLVER_CPU):at_cpu(RESOLVER_CPU)+9]=NEW_RESOLVER
    patched[FIRST_TEXT:END_TEXT]=b''.join(translated)+bytes(capacity-total)
    cursor=FIRST_TEXT;moved=0
    for rec,chunk in zip(records,translated):
        ptr=0x8000+(cursor-BANK6_START)
        at=int(rec['table_file_offset'],16)
        old=struct.unpack_from('<H',source,at)[0]
        if old!=ptr:moved+=1
        struct.pack_into('<H',patched,at,ptr)
        cursor+=len(chunk)
    if cursor!=FIRST_TEXT+total:raise AssertionError('Wrong packed cursor')
    for at in range(0x18010,0x18412,2):
        if at not in words and source[at:at+2]!=patched[at:at+2]:
            raise AssertionError('Pointer separator/sentinel changed')
    allowed=set(range(FIRST_TEXT,END_TEXT))
    allowed.update(k for p in words for k in (p,p+1))
    allowed.update(range(at_cpu(DISPATCH_CPU),at_cpu(DISPATCH_CPU)+4))
    allowed.update(range(at_cpu(RESOLVER_CPU),at_cpu(RESOLVER_CPU)+9))
    if any(i not in allowed for i,(a,b) in enumerate(zip(baseline,patched)) if a!=b):
        raise AssertionError('Unexpected change outside engine+Bank6')
    out=bytes(patched)
    fwd=v18.diff_ips(source,out);back=v18.diff_ips(out,source)
    if v16.apply_ips(source,fwd)!=out or v16.apply_ips(out,back)!=source:
        raise AssertionError('Cumulative IPS/rollback validation failed')
    report={'version':'v23-29-native-single-byte-tokens','source_sha256':SHA,
        'baseline_v17_sha256':r17['patched_sha256'],
        'patched_sha256':hashlib.sha256(out).hexdigest(),
        'forward_ips_sha256':hashlib.sha256(fwd).hexdigest(),
        'exact_rollback':True,'references_reencoded':sum(counts),
        'native_token_bytes':f'{FIRST_TOKEN:02X}..{LAST_TOKEN:02X}',
        'original_indexed_records':len(records),'moved_pointers':moved,
        'original_script_bytes':capacity,'repacked_script_bytes':total,
        'reclaimed_bank6_bytes':capacity-total,
        'additional_fixed_bank_engine_bytes_changed':sum(a!=b for a,b in zip(ORIG_DISPATCH+ORIG_RESOLVER,NEW_DISPATCH+NEW_RESOLVER)),
        'semantic_expansion_identical_for_all_479':True,
        'no_new_code_cave_needed':True,'fceux_runtime_verified':False,
        'remaining_risk':'Source code may read unindexed Bank6 $03 references; full emulator testing required.'}
    return fwd,back,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--out',type=Path,default=Path('work/v23'))
    args=p.parse_args();fw,rev,rep=build(read_source(args.rom))
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'Square_Tom_Sawyer_v23_29_OneByte_Tokens_EXPERIMENTAL.ips').write_bytes(fw)
    (args.out/'Square_Tom_Sawyer_v23_ROLLBACK_PRIVATE.ips').write_bytes(rev)
    (args.out/'manifest.json').write_text(json.dumps(rep,indent=2)+'\n',encoding='utf8')
    print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
