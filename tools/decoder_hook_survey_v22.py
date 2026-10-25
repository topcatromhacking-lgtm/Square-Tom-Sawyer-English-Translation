#!/usr/bin/env python3
"""Read-only survey of source-verified fixed-bank text reader and call sites.

No binary rewriting. In particular: long runs of FF/00 are NOT classified as
free code caves; screenshots/visual testing do not establish runtime hooks.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from analyze_rom import read_source
SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
FIXED_START=0x3C010
ROUTINES={
    'native_text_reader_EDC2':(0xEDC2,bytes.fromhex('08 48 8A 48 98 48 A9 06 20 D4 C3')),
    'native_ref_dispatch_EDE7':(0xEDE7,bytes.fromhex('C9 03 D0 06 20 FD ED')),
    'ref_state_dispatch_EDCD':(0xEDCD,bytes.fromhex('AD 80 79 F0 03 4C 2C EE')),
    'native_index_calc_EDFD':(0xEDFD,bytes.fromhex('A9 00 85 F2 20 92 ED')),
    'native_text_convert_EE50':(0xEE50,bytes.fromhex('C9 09 B0 01 60')),
    'bank_switch_C3D4':(0xC3D4,bytes.fromhex('EE 88 61 85 21 8D F9 FF')),
}
CALLS={
    'JSR_EDC2':bytes.fromhex('20 C2 ED'),
    'JMP_EDC2':bytes.fromhex('4C C2 ED'),
    'JSR_EE50':bytes.fromhex('20 50 EE'),
    'LDA_7980':bytes.fromhex('AD 80 79'),
    'STA_7980':bytes.fromhex('8D 80 79'),
    'JMP_EE2C':bytes.fromhex('4C 2C EE'),
}
def _runs(data:bytes,byte:int,min_count:int=24):
    start=None;result=[]
    for i,code in enumerate(data+b'\x7e'):
        if code==byte:
            if start is None:start=i
        elif start is not None:
            if i-start>=min_count:result.append({'cpu_start':f'{0xC000+start:04X}','bytes':i-start})
            start=None
    return result
def audit(source:bytes)->dict:
    if len(source)!=262160 or hashlib.sha256(source).hexdigest()!=SHA:
        raise ValueError('Expected exact Japanese source')
    bank=source[FIXED_START:FIXED_START+0x4000]
    for name,(cpu,signature) in ROUTINES.items():
        at=cpu-0xC000
        if bank[at:at+len(signature)]!=signature:
            raise ValueError(f'Unexpected {name} source bytes')
    callsites={}
    for name,code in CALLS.items():
        positions=[];cursor=0
        while True:
            at=bank.find(code,cursor)
            if at<0:break
            positions.append(f'{0xC000+at:04X}')
            cursor=at+1
        callsites[name]=positions
    return {'original_sha256':SHA,'fixed_bank':15,
        'source_anchored_routines':{key:f'{cpu:04X}' for key,(cpu,_) in ROUTINES.items()},
        'fixed_bank_raw_opcode_occurrences':callsites,
        'zero_runs_at_least_24_bytes':_runs(bank,0),
        'ff_runs_at_least_24_bytes':_runs(bank,255),
        'warning':'Raw opcode searches can match data; FF/00 runs may be graphics or tables, never automatic code caves.',
        'safety_conclusion':'No verified fixed-bank executable code cave or new 160-token decoder, and no Bank5/6 simultaneous PRG visibility.'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('--out',type=Path,default=Path('work/v22/hook_survey.json'))
    a=p.parse_args();x=audit(read_source(a.source))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
    print(json.dumps(x,indent=2))
if __name__=='__main__':main()
