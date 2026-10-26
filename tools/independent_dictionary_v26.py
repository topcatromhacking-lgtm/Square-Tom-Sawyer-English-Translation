#!/usr/bin/env python3
"""v26 experimental: relocate 29 native tokens to a separate Bank-6 pointer
 table and add token $ED -> an isolated English phrase 'HELLO'.

Uses FCEUX-confirmed v23 decoder and original-ROM-only cumulative IPS.
Replaces ONE diagnostic record B6-420 (four-byte original literal) with ED to exercise
new English dictionary path. No normal gameplay translation is claimed.

One JSR to the original common index helper is redirected to a byte-for-byte
clone in reclaimed Bank6; the clone has independent base-immediate operands.
Bank6 is presumed mapped during ED C2 native text handling; FCEUX runtime
confirmation of the *new* lookup is necessary before using production text.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from analyze_rom import get_record_map,read_source
from english_codec_v15 import encode
import native_onebyte_tokens_v23 as v23
import script_pipeline_v18 as v18

SOURCE_SHA=v23.SHA
PREVIOUS_SHA='27a3cd09f75714458929aaca3bee3c4777cdba9b1ee4cd89ebb2ab24f2c2394b'
TOTAL_RECORDS=479
TEXT_BEGIN=v23.FIRST_TEXT
TAIL_END=v23.END_TEXT
NEW_TOKEN=0xED  # old tokens D0..EC unchanged
PILOT_RECORD=420
NEW_PHRASE='HELLO'
JSR_SITE_CPU=0xEE0A
OLD_CALL=bytes.fromhex('20 9D ED')
# Exact original ED9D helper, 25 bytes; two immediate operands are independent.
HELPER_TEMPLATE=bytes.fromhex('8C 81 79 8D 82 79 0E 81 79 2E 82 79 AD 81 79 18 69 02 A8 AD 82 79 69 80 60')
assert len(HELPER_TEMPLATE)==25


def cpu_of(offset:int)->int:
    return 0x8000+offset-v23.BANK6_START


def putword(buffer:bytearray,pos:int,cpu:int):
    if not 0x8000<=cpu<0xC000:raise ValueError('Pointer escapes Bank 6')
    struct.pack_into('<H',buffer,pos,cpu)


def collect_bank6(rom:bytes,records:list[dict])->list[tuple[int,bytes]]:
    result=[]
    for i,rec in enumerate(records):
        pat=int(rec['table_file_offset'],16)
        cpu=struct.unpack_from('<H',rom,pat)[0]
        start=v23.BANK6_START+cpu-0x8000
        if i<len(records)-1:
            nextpat=int(records[i+1]['table_file_offset'],16)
            end=v23.BANK6_START+struct.unpack_from('<H',rom,nextpat)[0]-0x8000
        else:
            end=TEXT_BEGIN+14088
        blob=rom[start:end]
        if (start<TEXT_BEGIN or end>TAIL_END or len(blob)<3 or blob[-1]!=0 or
            b'\x00' in blob[2:-1]):
            raise ValueError(f'Invalid repacked record {i}')
        result.append((start,blob))
    if result[0][0]!=TEXT_BEGIN or result[-1][0]+len(result[-1][1])!=TEXT_BEGIN+14088:
        raise ValueError('v23 bank6 packed layout drift')
    return result


def compile(source:bytes)->tuple[bytes,bytes,dict]:
    if len(source)!=262160 or hashlib.sha256(source).hexdigest()!=SOURCE_SHA:
        raise ValueError('Exact unmodified Japanese ROM is required')
    patch,_,prev=v23.build(source)
    if prev['patched_sha256']!=PREVIOUS_SHA:raise ValueError('v23 fingerprint changed')
    base=v23.v16.apply_ips(source,patch)
    records,meta=get_record_map(source)
    if len(records)!=TOTAL_RECORDS:raise ValueError('Source Bank6 inventory changed')
    blobs=collect_bank6(base,records)
    # Exactly one known source-local string replaces the old shared alias.
    rec_start,rec=blobs[PILOT_RECORD]
    if rec!=b'\x00\x00\xc2\x8d\x64\x0b\x00':raise ValueError('B6-420 original literal fingerprint mismatch')
    result=bytearray(base)
    result[rec_start:rec_start+len(rec)]=b'\x00\x00\xed\x00'+bytes(len(rec)-4)
    # All indexed dialogue remains in place; independent table starts in the
    # 237 reclaimed bytes after the packed 479 original records.
    free_start=TEXT_BEGIN+14088
    helper_cpu=cpu_of(free_start)
    helper_len=26  # 25 instructions plus unreachable alignment NOP
    table_offset=free_start+helper_len
    table_cpu=cpu_of(table_offset)
    phrase_offset=table_offset+31*2  # sentinel + 30 entries
    phrase_cpu=cpu_of(phrase_offset)
    phrase_body=b'\x00\x00'+encode(NEW_PHRASE).data
    payload_end=phrase_offset+len(phrase_body)
    if not payload_end<=TAIL_END:raise ValueError('Bank6 dictionary tail overflow')
    if result[free_start:TAIL_END]!=b'\x00'*(TAIL_END-free_start):
        raise ValueError('v23 reclaimed bytes are not all zero')
    # Clone original common helper ($ED9D), patch its table base only.
    original_helper=source[v23.at_cpu(0xED9D):v23.at_cpu(0xED9D)+25]
    if original_helper!=HELPER_TEMPLATE:raise ValueError('Original helper bytes mismatch')
    helper=bytearray(HELPER_TEMPLATE)
    helper[17]=table_cpu&255
    helper[23]=(table_cpu>>8)&255
    result[free_start:table_offset]=bytes(helper)+b'\xEA'
    # Original 'index zero' table word is reserved; indexes 1..29 point to
    # their intact source records, index 30 to the independent English phrase.
    putword(result,table_offset,0xBFF7)
    for i in range(29):
        ptr_at=int(records[i]['table_file_offset'],16)
        original_ptr=struct.unpack_from('<H',base,ptr_at)[0]
        putword(result,table_offset+2*(i+1),original_ptr)
    putword(result,table_offset+60,phrase_cpu)
    result[phrase_offset:payload_end]=phrase_body
    if source[v23.at_cpu(JSR_SITE_CPU):v23.at_cpu(JSR_SITE_CPU)+3]!=OLD_CALL:
        raise ValueError('Existing resolver helper call changed')
    result[v23.at_cpu(JSR_SITE_CPU):v23.at_cpu(JSR_SITE_CPU)+3]=bytes([0x20,helper_cpu&255,helper_cpu>>8])
    # Check *all* 29 old tokens still resolve to their original shared records.
    for i in range(1,30):
        oldptr=struct.unpack_from('<H',base,int(records[i-1]['table_file_offset'],16))[0]
        newptr=struct.unpack_from('<H',result,table_offset+2*i)[0]
        if oldptr!=newptr:raise AssertionError('Existing token target changed')
    if struct.unpack_from('<H',result,table_offset+60)[0]!=phrase_cpu:
        raise AssertionError('English phrase lookup does not resolve')
    if result[phrase_offset:payload_end]!=phrase_body:
        raise AssertionError('English phrase data mismatch')
    if result[rec_start:rec_start+len(rec)]!=b'\x00\x00\xed\x00\x00\x00\x00':
        raise AssertionError('New source token not present')
    if any(base[int(r['table_file_offset'],16):int(r['table_file_offset'],16)+2]!=
           result[int(r['table_file_offset'],16):int(r['table_file_offset'],16)+2]
           for r in records):
        raise AssertionError('Original 479 dialogue pointers changed')
    allowed=set(range(free_start,payload_end))
    allowed.update(range(rec_start,rec_start+len(rec)))
    allowed.update(range(v23.at_cpu(JSR_SITE_CPU),v23.at_cpu(JSR_SITE_CPU)+3))
    deltas={i for i,(a,b) in enumerate(zip(base,result)) if a!=b}
    if deltas-allowed:raise AssertionError(f'Unexpected modifications outside authorized ranges: {sorted(deltas-allowed)[:5]}')
    output=bytes(result)
    fw=v18.diff_ips(source,output)
    rollback=v18.diff_ips(output,source)
    if v23.v16.apply_ips(source,fw)!=output or v23.v16.apply_ips(output,rollback)!=source:
        raise AssertionError('Reversible cumulative IPS failed')
    report={'version':'v26-independent-Bank6-phrase-table','original_sha256':SOURCE_SHA,
        'baseline_v23_sha256':PREVIOUS_SHA,'patched_sha256':hashlib.sha256(output).hexdigest(),
        'forward_ips_sha256':hashlib.sha256(fw).hexdigest(),'rollback_exact':True,
        'existing_native_tokens_preserved':29,'total_tokens':30,'new_token':'ED',
        'new_token_target':'isolated English HELLO','pilot_record':'B6-420',
        'primary_record_pointers_moved_since_v23':0,
        'jsr_patch_cpu':f'{JSR_SITE_CPU:04X}', 'helper_cpu':f'{helper_cpu:04X}',
        'dictionary_table_cpu':f'{table_cpu:04X}',
        'phrase_cpu':f'{phrase_cpu:04X}',
        'helper_bytes':helper_len,'pointer_table_bytes':62,
        'phrase_bytes':len(phrase_body),'tail_space_used':payload_end-free_start,
        'unused_tail_bytes':TAIL_END-payload_end,
        'runtime_new_lookup_verified':False,
        'note':'Experimental new token changes B6-420 output to HELLO; not a story-accurate translation. FCEUX text test pending.'}
    return fw,rollback,report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--out',type=Path,default=Path('work/v26'))
    ns=p.parse_args();fw,back,report=compile(read_source(ns.rom))
    ns.out.mkdir(parents=True,exist_ok=True)
    (ns.out/'Square_Tom_Sawyer_v26_Independent_Dictionary_Experimental.ips').write_bytes(fw)
    (ns.out/'Square_Tom_Sawyer_v26_ROLLBACK_PRIVATE.ips').write_bytes(back)
    (ns.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
