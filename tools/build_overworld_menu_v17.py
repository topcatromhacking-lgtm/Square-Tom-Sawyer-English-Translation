#!/usr/bin/env python3
"""v1.7 four direct-tile English overworld commands, cumulative with v1.6.

Checksum-gated original Japanese ROM only. Writes IPS + local rollback; never
writes a new ROM image. The v1.6 English event/dialogue patch is reproduced
byte-for-byte and not stacked with any externally supplied IPS.
"""
import argparse,hashlib,json
from pathlib import Path
from analyze_rom import read_source
import build_opening_v16 as v16

SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
BASE_SHA='9709c1df01b9fb304ee9dd39f5dd48afe43aaf346827b83f9ab353dd18cae4ba'
BASE_IPS_SHA='b96f5b34816439d24437ea816f66004c878bb75b0ee55c7b63c48624fba2f06e'
# Tile positions independently identified in both original and historical 2.0.
MENU_FIELDS=((0x3D1AF,bytes.fromhex('A3 BE B4 7E C0'),'LOOK'),
             (0x3D1B6,bytes.fromhex('AB C0 FF FF'),'TAKE'),
             (0x3D1BF,bytes.fromhex('FF B5 C0'),'DIG'),
             (0x3D1C8,bytes.fromhex('CE CF E0 EE'),'ITEM'))

def tiles(word,capacity):
    if not word.isalpha() or not word.isupper() or len(word)>capacity:
        raise ValueError('Invalid fixed-length menu label')
    return bytes(0xDE+ord(c)-65 for c in word)+b'\xff'*(capacity-len(word))

def ips_records(ips):
    if not ips.startswith(b'PATCH') or not ips.endswith(b'EOF'):raise ValueError('Invalid IPS')
    pos=5;records=[];occupied=set()
    while pos<len(ips)-3:
        at=int.from_bytes(ips[pos:pos+3],'big');n=int.from_bytes(ips[pos+3:pos+5],'big');pos+=5
        if n==0 or pos+n>len(ips)-3:raise ValueError('Malformed IPS record')
        region=set(range(at,at+n))
        if region&occupied:raise ValueError('Overlapping IPS records')
        occupied|=region;records.append((at,ips[pos:pos+n]));pos+=n
    if pos!=len(ips)-3:raise ValueError('Unexpected IPS trailer')
    return records

def build(original):
    if len(original)!=262160 or hashlib.sha256(original).hexdigest()!=SHA:
        raise ValueError('Wrong unmodified original Japanese ROM')
    base,back,_=v16.build(original)
    if hashlib.sha256(base).hexdigest()!=BASE_IPS_SHA:
        raise AssertionError('v1.6 generator changed')
    prior=v16.apply_ips(original,base)
    if hashlib.sha256(prior).hexdigest()!=BASE_SHA:
        raise AssertionError('v1.6 baseline changed')
    changed=[];restore=[]
    for at,expected,word in MENU_FIELDS:
        if original[at:at+len(expected)]!=expected or prior[at:at+len(expected)]!=expected:
            raise ValueError('Original menu byte mismatch')
        changed.append((at,tiles(word,len(expected))))
        restore.append((at,expected))
    forward=v16.make_ips(ips_records(base)+changed)
    reverse=v16.make_ips(ips_records(back)+restore)
    final=v16.apply_ips(original,forward)
    if v16.apply_ips(final,reverse)!=original:
        raise AssertionError('Rollback did not restore exact source')
    allowed={at+i for at,expected,_ in MENU_FIELDS for i in range(len(expected))}
    changed_bytes={i for i,(a,b) in enumerate(zip(prior,final)) if a!=b}
    if changed_bytes!=allowed or len(final)!=len(original) or final[:16]!=original[:16]:
        raise AssertionError('Changes escaped fixed-bank menu fields')
    return forward,reverse,{'version':'v1.7','source_sha256':SHA,
        'patched_sha256':hashlib.sha256(final).hexdigest(),
        'rollback_sha256':hashlib.sha256(v16.apply_ips(final,reverse)).hexdigest(),
        'menu_labels':[w for _,_,w in MENU_FIELDS],
        'menu_bytes_changed':len(changed_bytes),'forward_ips_bytes':len(forward),
        'v16_opening_preserved':True,'fceux_runtime_verified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--out',type=Path,default=Path('work/v17'))
    a=p.parse_args();fw,rv,manifest=build(read_source(a.rom))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'Square_Tom_Sawyer_English_Overworld_v17.ips').write_bytes(fw)
    (a.out/'Square_Tom_Sawyer_English_Overworld_v17_ROLLBACK.ips').write_bytes(rv)
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
