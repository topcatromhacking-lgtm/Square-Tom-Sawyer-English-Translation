#!/usr/bin/env python3
"""Historical Square no Tom Sawyer IPS forensics: source-only, no ROM outputs.

Usage: python tools/audit_historical_ips.py "Square no Tom Sawyer (Japan).zip" tomsawee.zip t-snts2.zip
The complete standalone audit + 8 tests also shipped with the user's ZIP.
"""
from collections import Counter
import hashlib, json, struct, sys, zipfile
from pathlib import Path

SOURCE_SHA256 = 'ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
SIZE = 262160

def readzip(path,ext):
    with zipfile.ZipFile(path) as z:
        entries=[x for x in z.namelist() if x.lower().endswith(ext)]
        if len(entries)!=1:raise ValueError(f'Expected one {ext} in {path}')
        return entries[0],z.read(entries[0])

def read_records(ips):
    if not ips.startswith(b'PATCH'):raise ValueError('Invalid IPS header')
    idx=5;records=[]
    while idx<len(ips):
        if ips[idx:idx+3]==b'EOF':
            if idx+3!=len(ips):raise ValueError('Unexpected IPS tail')
            return records
        if idx+5>len(ips):raise ValueError('Truncated IPS')
        offset=int.from_bytes(ips[idx:idx+3],'big')
        count=int.from_bytes(ips[idx+3:idx+5],'big');idx+=5
        if count:
            dat=ips[idx:idx+count]
            if len(dat)!=count:raise ValueError('Truncated IPS payload')
            idx+=count
        else:
            if idx+3>len(ips):raise ValueError('Truncated RLE IPS')
            repeats=int.from_bytes(ips[idx:idx+2],'big')
            dat=bytes([ips[idx+2]])*repeats;idx+=3
        if not dat or offset+len(dat)>SIZE:raise ValueError('Out-of-range IPS record')
        records.append((offset,dat))
    raise ValueError('IPS missing EOF')

def apply(original,records):
    result=bytearray(original)
    used=set()
    for offset,dat in records:
        written=set(range(offset,offset+len(dat)))
        if used&written:raise ValueError('IPS overlap')
        used.update(written)
        result[offset:offset+len(dat)]=dat
    return bytes(result)

def main(original_zip,patch_zip1,patch_zip2):
    _,orig=readzip(original_zip,'.nes')
    if len(orig)!=SIZE or hashlib.sha256(orig).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Clean Japanese source required')
    pointers=[]
    for at in range(0x18014,0x18412,2):
        ptr=struct.unpack_from('<H',orig,at)[0]
        if ptr!=0xffff:pointers.append(0x18010+ptr-0x8000)
    assert len(pointers)==479
    ends=[next_ptr-1 for next_ptr in pointers[1:]+[0x1c007]]
    result=[];variants=[]
    for zp in [patch_zip1,patch_zip2]:
        name,ips=readzip(zp,'.ips')
        p=apply(orig,read_records(ips))
        differences={i for i,(x,y) in enumerate(zip(orig,p)) if x!=y}
        changed=lambda lo,hi:sum(lo<=x<hi for x in differences)
        count=Counter((x-16)//0x4000 for x in differences)
        latin_base=0x5e if name.upper()=='TOMSAWEE.IPS' else 0x6e
        report={
          'patch':name,'ips_bytes':len(ips),'rom_size':len(p),
          'patched_sha256':hashlib.sha256(p).hexdigest(),
          'actually_changed_bytes':len(differences),
          'changed_prg_banks':dict(sorted(count.items())),
          'font_changed_bytes':changed(0x17710,0x17b88),
          'spare_font_changed_bytes':changed(0x17b88,0x18010),
          'dialogue_pointer_bytes_changed':changed(0x18010,0x18412),
          'decoder_EE50_bytes_changed':changed(0x3ee60,0x3eeb0),
          'font_upload_C587_bytes_changed':changed(0x3c597,0x3c680),
          'indexed_record_ends_overwritten':sum(orig[i]==0 and p[i]!=0 for i in ends),
          'indexed_records_touched':sum(any(i in differences for i in range(s,e))
             for s,e in zip(pointers,pointers[1:]+[0x1c007])),
          'latin_A_code':f'{latin_base:02X}', 'latin_Z_code':f'{latin_base+25:02X}'
        }
        result.append(report);variants.append((p,differences))
    (x,a),(y,b)=variants
    comparison={'overlapping_changed_offsets':len(a&b),
                'same_replacement_bytes_in_overlap':sum(x[i]==y[i] for i in a&b),
                'patched_ROMs_are_alternative_not_stackable':True}
    print(json.dumps({'source_sha256':SOURCE_SHA256,'predecessors':result,
                      'comparison':comparison},indent=2))
if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: audit_historical_ips.py ORIGINAL.zip OLD.zip VERSION2.zip')
    main(*map(Path,sys.argv[1:]))
