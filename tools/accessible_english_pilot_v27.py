#!/usr/bin/env python3
"""v27 accessible English phrase test in source-verified Bank6 record B6-356.

Experimental standalone cumulative IPS: preserve original 479 pointer words,
the 29 native phrase targets, the proven independent dictionary helper and the
v1.7 opening/menu. This is NOT a complete or visually accepted translation.
The user v26b live log located record B6-356 at primary_next=$B861.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from analyze_rom import read_source,get_record_map
from english_codec_v15 import encode
import native_onebyte_tokens_v23 as v23
import independent_dictionary_v26 as v26
import script_pipeline_v18 as v18

ORIGINAL_SHA=v23.SHA
V23_SHA=v26.PREVIOUS_SHA
TARGET=356
PHRASES=((0xED,"THERE'S NOTHING"),(0xEE,"FOR YOU HERE."),
         (0xEF,"THE ANGEL WHISPERED."))
NEW_BODY=bytes.fromhex('EF 02 01 ED 01 EE 00')
HELPER=0x1BF1A
TABLE=0x1BF34

def record_slice(rom,records,index):
    a=int(records[index]['table_file_offset'],16)
    b=int(records[index+1]['table_file_offset'],16)
    start=0x18010+struct.unpack_from('<H',rom,a)[0]-0x8000
    stop=0x18010+struct.unpack_from('<H',rom,b)[0]-0x8000
    return start,stop,rom[start:stop]

def build(original:bytes):
    if len(original)!=262160 or hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('Exact original Japanese ROM SHA-256 required')
    v23_ips,_,r23=v23.build(original)
    if r23['patched_sha256']!=V23_SHA:raise AssertionError('v23 checksum changed')
    base=v23.v16.apply_ips(original,v23_ips)
    records,_=get_record_map(original)
    if len(records)!=479:raise AssertionError('Indexed script changed')
    start,stop,old=record_slice(base,records,TARGET)
    if start!=0x1B86E or len(old)!=22 or old[:5]!=bytes.fromhex('00 00 DD 02 01'):
        raise ValueError('B6-356 original/header/control fingerprint changed')
    if start+3!=0x18010+0xB861-0x8000:
        raise ValueError('User observed primary_next=$B861 no longer matches')
    out=bytearray(base)
    out[start:stop]=old[:2]+NEW_BODY+bytes(len(old)-2-len(NEW_BODY))
    if base[HELPER:0x1C007]!=bytes(0x1C007-HELPER):
        raise ValueError('The source-derived reclaimed tail is not blank')
    helper=bytearray(v26.HELPER_TEMPLATE)
    table_cpu=v26.cpu_of(TABLE)
    helper[17]=table_cpu&0xff
    helper[23]=table_cpu>>8
    out[HELPER:TABLE]=helper+b'\xEA'
    v26.putword(out,TABLE,0xBFF7)
    for index in range(1,30):
        at=int(records[index-1]['table_file_offset'],16)
        target=struct.unpack_from('<H',base,at)[0]
        v26.putword(out,TABLE+index*2,target)
    cursor=TABLE+2*(1+29+len(PHRASES))
    phrase_report=[]
    for index,(token,text) in enumerate(PHRASES,30):
        if index!=token-0xCF or len(text)>20:raise ValueError('Token namespace/width error')
        encoded=b'\0\0'+encode(text,maximum_lines=1,maximum_chars_per_line=20).data
        v26.putword(out,TABLE+index*2,v26.cpu_of(cursor))
        out[cursor:cursor+len(encoded)]=encoded
        phrase_report.append({'token':f'{token:02X}','index':index,
                              'english':text,'cpu_pointer':f'{v26.cpu_of(cursor):04X}',
                              'encoded_bytes':len(encoded)})
        cursor+=len(encoded)
    if cursor>0x1C007:raise ValueError('Bank6 dictionary overflow')
    pos=v23.at_cpu(0xEE0A)
    if base[pos:pos+3]!=v26.OLD_CALL:raise ValueError('Native JSR changed')
    helper_cpu=v26.cpu_of(HELPER)
    out[pos:pos+3]=bytes((0x20,helper_cpu&255,helper_cpu>>8))
    for r in records:
        at=int(r['table_file_offset'],16)
        if out[at:at+2]!=base[at:at+2]:raise AssertionError('Main pointer changed')
    for index in range(1,30):
        at=int(records[index-1]['table_file_offset'],16)
        if out[TABLE+index*2:TABLE+index*2+2]!=base[at:at+2]:
            raise AssertionError('Original shared phrase target changed')
    changed={i for i,(a,b) in enumerate(zip(base,out)) if a!=b}
    allowed=set(range(start,stop))|set(range(HELPER,cursor))|set(range(pos,pos+3))
    if changed-allowed:raise AssertionError('Changed ROM bytes outside approved ranges')
    if out[0x2124D:0x213EC]!=base[0x2124D:0x213EC] or \
       out[0x3D1AF:0x3D1CB]!=base[0x3D1AF:0x3D1CB]:
        raise AssertionError('Opening or English menus changed')
    output=bytes(out)
    fw=v18.diff_ips(original,output)
    back=v18.diff_ips(output,original)
    if v23.v16.apply_ips(original,fw)!=output or \
       v23.v16.apply_ips(output,back)!=original:
        raise AssertionError('Exact cumulative patch or rollback failure')
    report={'version':'v27-accessible-English-dictionary-pilot',
            'source_sha256':ORIGINAL_SHA,'previous_v23_sha256':V23_SHA,
            'patched_sha256':hashlib.sha256(output).hexdigest(),
            'forward_ips_sha256':hashlib.sha256(fw).hexdigest(),
            'rollback_exact':True,'source_record':TARGET,
            'observed_primary_next':'B861','pilot_record_cpu':'B85E',
            'pilot_record_before_hex':old.hex(),
            'pilot_record_after_hex':out[start:stop].hex(),
            'dictionary_token_count':32,'new_phrase_tokens':phrase_report,
            'dictionary_table_cpu':f'{table_cpu:04X}',
            'helper_cpu':f'{helper_cpu:04X}',
            'dictionary_end_file':f'{cursor:05X}',
            'free_tail_bytes':0x1C007-cursor,
            'primary_game_dialogue_pointer_edits':0,
            'old_b6_420_diagnostic_removed':True,
            'runtime_verified':False,
            'visual_width_test':'PENDING FCEUX - new English phrase and 02/01 controls'}
    return fw,back,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original',type=Path)
    p.add_argument('--out',type=Path,default=Path('work/v27'))
    a=p.parse_args()
    fw,back,report=build(read_source(a.original))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'Square_Tom_Sawyer_v27_Accessible_English_Dictionary_EXPERIMENTAL.ips').write_bytes(fw)
    (a.out/'Square_Tom_Sawyer_v27_ROLLBACK_PRIVATE.ips').write_bytes(back)
    (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
