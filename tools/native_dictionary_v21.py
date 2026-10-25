#!/usr/bin/env python3
"""Read-only original text-reference audit and nonnested phrase-dictionary model.

This is NOT a working NES decoder, translation patch or bank-switching routine.
All token IDs are abstract integers above 255, not assigned real NES byte codes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
from analyze_rom import read_source,get_record_map

SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
BANK5_FREE_START=0x17B88
BANK5_FREE_END=0x18010
BANK6_CAPACITY=14325

def audit_native(rom:bytes)->dict:
    if hashlib.sha256(rom).hexdigest()!=SHA:
        raise ValueError('Only exact original Japanese ROM accepted')
    rows,_=get_record_map(rom)
    if len(rows)!=479:raise AssertionError('Unexpected indexed Bank 6 record count')
    # Disassembled fixed-bank CPU: ED C2 reader; ED FD reference helper;
    # EE 2C secondary reader. A 03 index points to Bank6 $8002+2*index.
    signatures={0xEDD9:bytes.fromhex('d0 09 8d 1a 62'),
                0xEDE7:bytes.fromhex('c9 03 d0 06'),
                0xEE1C:bytes.fromhex('ee 80 79'),
                0xEE2E:bytes.fromhex('a1 f7 c9 02'),
                0xEE41:bytes.fromhex('20 25 ee 20 50 ee')}
    for pc,opcodes in signatures.items():
        at=0x3C010+(pc-0xC000)
        if rom[at:at+len(opcodes)]!=opcodes:
            raise ValueError(f'Unknown decoder code at CPU {pc:04X}')
    targets=Counter();callers=set();body_codes=Counter()
    for rec in rows:
        at=int(rec['text_file_offset'],16)
        raw=rom[at:at+rec['length_bytes']]
        i=2
        while i<len(raw)-1:
            if raw[i]!=3:
                body_codes[raw[i]]+=1;i+=1;continue
            if i+1>=len(raw)-1:raise ValueError('Truncated 03 reference')
            index=raw[i+1]
            if not 1<=index<=251:raise ValueError('Native reference outside first pointer group')
            target=rows[index-1]
            if int(target['table_file_offset'],16)!=0x18012+2*index:
                raise ValueError('Native index pointer mismatch')
            targets[index]+=1
            callers.add(rec['global_index'])
            i+=2
    nested=[]
    for index in targets:
        target=rows[index-1];at=int(target['text_file_offset'],16)
        original=rom[at:at+target['length_bytes']]
        if 3 in original[2:-1]:nested.append(index)
    if nested:raise ValueError('Native phrase references are nested; review interpreter')
    zero=rom[BANK5_FREE_START:BANK5_FREE_END]
    return {'source_sha256':SHA,'indexed_bank6_records':len(rows),
        'native_reference_control':'03 <one-byte index>',
        'native_reference_occurrences':sum(targets.values()),
        'unique_reference_targets':len(targets),'target_indexes':sorted(targets),
        'referencing_source_records':len(callers),'nested_reference_targets':nested,
        'absent_unmodified_body_byte_values':sum(body_codes[b]==0 for b in range(256)),
        'token_namespace_risk':'Cannot assume 160 unused token bytes in original untranslated Bank6',
        'bank5_zero_region_file_offsets':'17B88..1800F',
        'bank5_zero_region_bytes':len(zero),'bank5_region_is_all_zero':not any(zero),
        'implementation':'Read-only analysis; no custom decoder, token IDs or Bank5 switching'}

def estimate_flat(texts:list[str],*,token_limit:int=160,max_phrase_length:int=13,
                  checkpoints=(0,64,96,128,144,160,176,190))->dict:
    if not 0<=token_limit<=190:raise ValueError('Token limit must be 0..190')
    if not 2<=max_phrase_length<=32:raise ValueError('Phrase length must be 2..32')
    if not texts or any(not isinstance(s,str) or any(ord(c)>127 for c in s) for s in texts):
        raise ValueError('All records must be ASCII; no lossy Unicode filtering')
    source=[s.upper().replace('\\n','\n') for s in texts]
    sequences=[list(map(ord,s)) for s in source]
    phrases=[];stats=[]
    def snapshot(n):
        symbols=sum(len(x) for x in sequences)
        data_bytes=sum(len(p)+1 for p in phrases)
        ptr_bytes=2*len(phrases)
        stats.append({'tokens':n,'estimated_bank6_bytes':symbols+3*len(source),
            'bank6_margin':BANK6_CAPACITY-symbols-3*len(source),
            'dictionary_data_bytes':data_bytes,
            'dictionary_index_bytes':ptr_bytes,
            'total_dictionary_storage':data_bytes+ptr_bytes,
            'bank5_spare_margin':BANK5_FREE_END-BANK5_FREE_START-data_bytes-ptr_bytes})
    snapshot(0)
    for n in range(1,token_limit+1):
        freq=Counter()
        for seq in sequences:
            s=''.join(chr(c) if 32<=c<=126 else '\0' for c in seq)
            for size in range(2,max_phrase_length+1):
                for k in range(len(s)-size+1):
                    word=s[k:k+size]
                    if '\0' not in word:freq[word]+=1
        best=max((w for w,c in freq.items() if c>=2),
                 key=lambda w:((len(w)-1)*freq[w],freq[w],len(w),w),default=None)
        if not best:break
        word=list(map(ord,best));token=256+n;phrases.append(best)
        replaced=[]
        for row in sequences:
            output=[];i=0
            while i<len(row):
                if row[i:i+len(word)]==word:
                    output.append(token);i+=len(word)
                else:output.append(row[i]);i+=1
            replaced.append(output)
        sequences=replaced
        if n in checkpoints:snapshot(n)
    if len(phrases) not in [r['tokens'] for r in stats]:snapshot(len(phrases))
    mapping={i+257:w for i,w in enumerate(phrases)}
    roundtrip=[''.join(mapping[c] if c>255 else chr(c) for c in row) for row in sequences]
    if roundtrip!=source:raise AssertionError('Lossless flat-dictionary roundtrip failed')
    return {'source_characters':sum(map(len,source)), 'records':len(source),
        'drafts':sum(bool(s) for s in texts),'non_nested_phrase_tokens':len(phrases),
        'estimates':stats,'lossless_abstract_roundtrip':True,
        'warning':'Does not implement actual NES token codes, line fitting, control bytes, decoder or bank switching.'}

def load_english(tsv:Path)->list[str]:
    with tsv.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    if len(rows)!=520 or any(r.get('bank')!='6' for r in rows[:479]):
        raise ValueError('Requires intact 520-record v1.8 private TSV')
    return [r.get('english','') for r in rows[:479]]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=Path('work/v21/native_dictionary_audit.json'))
    cmd=p.add_subparsers(dest='command',required=True)
    a=cmd.add_parser('native');a.add_argument('rom',type=Path)
    b=cmd.add_parser('flat');b.add_argument('tsv',type=Path)
    b.add_argument('--tokens',type=int,default=160)
    args=p.parse_args()
    report=audit_native(read_source(args.rom)) if args.command=='native' else estimate_flat(load_english(args.tsv),token_limit=args.tokens)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
