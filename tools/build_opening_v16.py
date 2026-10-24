#!/usr/bin/env python3
"""Build a guarded, reversible v1.6 English opening IPS from the exact clean NES ROM.

Translates exactly twelve consecutive opening records; not a first-quest release.
No copyrighted ROM or older fan translation patch is written to Git.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from analyze_rom import read_source
from english_codec_v15 import ALPHABET, PUNCTUATION, encode
from make_english_intro_v11 import HEX_GLYPHS

ORIGINAL_SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
SOURCE_LEN=262160
TEXT_START,TEXT_END=0x2129f,0x213ec
TABLE,BANK8=0x2124d,0x20010
TEXTS=(
'UNITED STATES\nMISSOURI\n1855, ONE NIGHT',
"WHERE AM I?\nWHAT'S THAT TOWN?",
"TOM, IT'S SOUTHWEST.",
'SOUTHWEST?\nNEVER HEARD OF IT.',
'PIRATE TREASURE\nIS HIDDEN IN TOWN.',
'REALLY?',
"JIM! AMY! HURRY!\nTHE BOAT'S LEAVING!",
"HUCK! I'M COMING!",
'SORRY, TOM!\nONLY THREE TICKETS.',
'HUCK! JIM! WAIT!',
'WAIT! HUCK!\nJIM! AMY!',
"TOM! WAKE UP!\nYOU'VE SLEPT ENOUGH!",
)
# All new, independently drawn punctuation bitmap rows.
PUNCT_BITMAPS={"'":'0018181020000000','-':'000000003c000000',
',':'0000000000001810','.':'0000000000001818',
'!':'0018181818001800','?':'0038440408100010'}

def make_ips(records):
    out=bytearray(b'PATCH')
    for at,data in sorted(records):
        if at<0 or at+len(data)>SOURCE_LEN or not 0<len(data)<=65535:raise ValueError('IPS bounds')
        out+=at.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
    return bytes(out+b'EOF')

def apply_ips(source,ips):
    if not ips.startswith(b'PATCH') or not ips.endswith(b'EOF'):raise ValueError('Bad IPS')
    data=bytearray(source);at=5
    while at<len(ips)-3:
        off=int.from_bytes(ips[at:at+3],'big');n=int.from_bytes(ips[at+3:at+5],'big');at+=5
        if n<1 or off+n>len(data) or at+n>len(ips)-3:raise ValueError('Invalid IPS record')
        data[off:off+n]=ips[at:at+n];at+=n
    if at!=len(ips)-3:raise ValueError('IPS trailer')
    return bytes(data)

def build(source):
    if len(source)!=SOURCE_LEN or hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('Wrong ROM (source must be unmodified Japanese original)')
    pointers=[struct.unpack_from('<H',source,TABLE+2*i)[0] for i in range(13)]
    offsets=[BANK8+x-0x8000 for x in pointers]
    if offsets[0]!=TEXT_START or offsets[12]!=TEXT_END or any(a>=b for a,b in zip(offsets,offsets[1:])):
        raise ValueError('Unexpected bank-8 original pointer layout')
    for i in range(12):
        blob=source[offsets[i]:offsets[i+1]]
        if not blob or blob[-1]!=0 or 0 in blob[:-1]:raise ValueError('Unexpected interior null/metadata')
    encoded=[encode(s,maximum_lines=3 if i==0 else 2,maximum_chars_per_line=20).data for i,s in enumerate(TEXTS)]
    used=sum(map(len,encoded));capacity=TEXT_END-TEXT_START
    if used>capacity:raise ValueError('Text window overflow')
    out=bytearray(source);changed=set();fwd=[];undo=[]
    def edit(at,data):
        indices=set(range(at,at+len(data)))
        if not data or at<0 or at+len(data)>len(source) or changed&indices:
            raise ValueError('Overlapping/out-of-bounds IPS edits')
        changed.update(indices)
        old=source[at:at+len(data)]
        if old!=data:
            out[at:at+len(data)]=data;fwd.append((at,data));undo.append((at,old))
    for c,code in ALPHABET.items():edit(0x17710+code*8,bytes.fromhex(HEX_GLYPHS[c]))
    for c,glyph in PUNCT_BITMAPS.items():edit(0x17710+PUNCTUATION[c]*8,bytes.fromhex(glyph))
    edit(TEXT_START,b''.join(encoded)+bytes(capacity-used))
    cursor=TEXT_START;moves=[]
    for i,raw in enumerate(encoded):
        ptr=0x8000+cursor-BANK8
        if not 0x8000<=ptr<0xC000:raise ValueError('Pointer escapes bank')
        if pointers[i]!=ptr:moves.append((i,pointers[i],ptr))
        edit(TABLE+i*2,struct.pack('<H',ptr))
        cursor+=len(raw)
    if struct.unpack_from('<H',out,TABLE+24)[0]!=pointers[12] or out[TEXT_END:]!=source[TEXT_END:]:
        raise AssertionError('Modified following dialogue')
    if out[:16]!=source[:16] or len(out)!=len(source):raise AssertionError('ROM/header changed')
    if any(i not in changed for i,(a,b) in enumerate(zip(source,out)) if a!=b):
        raise AssertionError('Change escaped bounded patch ranges')
    forward,rollback=make_ips(fwd),make_ips(undo)
    if apply_ips(source,forward)!=bytes(out) or apply_ips(out,rollback)!=source:
        raise AssertionError('Byte-exact patch and rollback failed')
    report=dict(version='1.6',original_sha256=ORIGINAL_SHA,
                patched_sha256=hashlib.sha256(out).hexdigest(),
                rollback_sha256=hashlib.sha256(apply_ips(out,rollback)).hexdigest(),
                edited_records=12,moved_pointers=len(moves),pointer_changes=[
                    dict(record=i,old=f'{old:04X}',new=f'{new:04X}') for i,old,new in moves],
                capacity_bytes=capacity,encoded_bytes=used,free_padding_bytes=capacity-used,
                forward_ips_bytes=len(forward),fceux_verified=False)
    return forward,rollback,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original_rom',type=Path);p.add_argument('--out',type=Path,default=Path('work/v16'))
    a=p.parse_args();fw,rv,report=build(read_source(a.original_rom))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'Square_Tom_Sawyer_English_Opening_v16.ips').write_bytes(fw)
    (a.out/'Square_Tom_Sawyer_English_Opening_v16_ROLLBACK.ips').write_bytes(rv)
    (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
