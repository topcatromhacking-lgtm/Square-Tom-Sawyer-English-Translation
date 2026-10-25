#!/usr/bin/env python3
"""Read-only dictionary-token compression feasibility for private English TSV.

This models two-character (DTE-style) pair substitution; it does NOT patch
an NES ROM or establish that its decoder can interpret the proposed tokens.
TSV translation drafts are private. Report only aggregate counts and estimates.
"""
from __future__ import annotations
import argparse,csv,json
from collections import Counter
from pathlib import Path

BANK6_CAPACITY=14325
BANK6_RECORDS=479

def compress(records:list[str],*,max_tokens:int=190,checkpoints:tuple[int,...]=(16,32,64,96,112,128,144,160,176,190)):
    if max_tokens<0 or max_tokens>190:raise ValueError('Token budget must be 0..190')
    strings=[list(s.upper()) for s in records]
    original=sum(map(len,strings))
    out=[];dictionary=[]
    points=sorted(set([0,max_tokens,*[c for c in checkpoints if c<=max_tokens]]))
    def snapshot(n):
        current=sum(map(len,strings));needed=current+len(strings)*3
        out.append({'dictionary_tokens':n,'visible_symbols':current,
                    'minimum_record_bytes':needed,'original_bank_capacity':BANK6_CAPACITY,
                    'margin_bytes':BANK6_CAPACITY-needed,'dictionary_bytes_outside_bank':2*n,
                    'source_header_and_end_bytes':3*len(strings)})
    snapshot(0)
    for round in range(1,max_tokens+1):
        pairs=Counter()
        for entry in strings:
            pairs.update(zip(entry,entry[1:]))
        if not pairs:break
        (a,b),f=pairs.most_common(1)[0]
        if f<3:break
        token=chr(0xe000+round) # simulated symbol, not an NES byte assignment
        new=[];hits=0
        for entry in strings:
            encoded=[];i=0
            while i<len(entry):
                if i+1<len(entry) and entry[i]==a and entry[i+1]==b:
                    encoded.append(token);i+=2;hits+=1
                else:
                    encoded.append(entry[i]);i+=1
            new.append(encoded)
        strings=new;dictionary.append((a,b,hits))
        if round in points:snapshot(round)
    if len(dictionary) not in [x['dictionary_tokens'] for x in out]:snapshot(len(dictionary))
    return {'records_modeled':len(records),'characters_before':original,
            'token_dictionary_entries':len(dictionary),'estimates':out,
            'warning':'Optimistic model only: excludes explicit line breaks, custom control codes, screen fitting, dictionary decoder, token byte assignment and runtime banking.'}

def load_bank6_english(tsv:Path):
    with tsv.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter='\t');rows=list(reader)
    if len(rows)!=520 or any(r.get('bank')!='6' for r in rows[:BANK6_RECORDS]):
        raise ValueError('Expected intact 520-record v1.8 private TSV')
    return [r['english'].replace('\\n',' ') for r in rows[:BANK6_RECORDS]]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_tsv',type=Path)
    p.add_argument('--tokens',type=int,default=190)
    p.add_argument('--out',type=Path,default=Path('work/v20/dte_capacity.json'))
    a=p.parse_args();texts=load_bank6_english(a.private_tsv)
    report=compress(texts,max_tokens=a.tokens)
    report['entries_with_draft']=sum(bool(s) for s in texts)
    report['entries_without_draft']=sum(not s for s in texts)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
