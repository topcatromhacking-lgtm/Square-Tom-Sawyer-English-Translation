#!/usr/bin/env python3
"""v2.0 Bank-6 script packer: bulk repoint *within existing 14,325-byte bank allocation*.

Use the same SHA-pinned source and private TSV as v1.8. All 479 original
headers, pointer ordering, FFFF delimiters, and non-script bytes are preserved.
Long approved English records are permitted when shorter neighbors compensate.
This is structural verification, NOT proof that no runtime hardcoded reference
exists. No additional banks or ROM expansion are implemented.

  python tools/script_pipeline_v20.py plan ORIGINAL.zip work/script/master_PRIVATE.tsv
  python tools/script_pipeline_v20.py build ORIGINAL.zip work/script/master_PRIVATE.tsv --out work/v20
Complex two-byte header replacement requires --allow-complex-header explicitly.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from analyze_rom import read_source, get_record_map
from english_codec_v15 import encode
import script_pipeline_v18 as v18

SOURCE_SHA = 'ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
BANK6_TABLE = 0x18010
BANK6_START = 0x18812
BANK6_END = 0x1C007
END_CPU_PTR = 0xBFF7
SIMPLE = b'\x00\x00'


def encode_preserving_header(original:bytes, english:str, *, allow_complex_header=False)->bytes:
    """Pure transformation: keep the original two metadata bytes unmodified."""
    if len(original)<3 or original[-1]!=0 or b'\x00' in original[2:-1]:
        raise ValueError('Invalid original record termination')
    if original[:2]!=SIMPLE and not allow_complex_header:
        raise ValueError('complex header requires --allow-complex-header')
    if not english:
        raise ValueError('Approved record lacks English')
    encoded=encode(english.replace('\\n','\n'),maximum_lines=2,
                   maximum_chars_per_line=20).data
    return original[:2]+encoded


def pack_original_window(parts:list[bytes],capacity:int)->bytes|None:
    """Pure in-bank text allocator; None means fail closed on overflow."""
    if capacity<=0 or not parts or any(not p or p[-1]!=0 for p in parts):
        raise ValueError('Invalid text window or broken record termination')
    joined=b''.join(parts)
    return joined+bytes(capacity-len(joined)) if len(joined)<=capacity else None


def compile_bank6(source: bytes, baseline: bytes, rows: list[dict], *, allow_complex_header=False):
    """Return a complete ROM after exact-bounds packing and a detailed plan.

    The rows must originate from v1.8 load_edited source-locking. Every
    unchanged record is copied byte-for-byte, including unknown controls.
    """
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA:
        raise ValueError('Wrong original Japanese ROM SHA-256')
    if len(source)!=262160 or len(baseline)!=len(source):
        raise ValueError('Invalid original/baseline length')
    if len(rows)!=520:
        raise ValueError('Expected full 520-record private TSV')
    records,summary=get_record_map(source)
    if len(records)!=479 or summary['group_counts']!=[251,35,123,70]:
        raise ValueError('Unexpected source pointer groups')
    if baseline[BANK6_TABLE:BANK6_END]!=source[BANK6_TABLE:BANK6_END]:
        raise ValueError('Baseline already edits Bank 6, refusing to layer patch')
    if struct.unpack_from('<H',source,BANK6_TABLE)[0]!=END_CPU_PTR:
        raise ValueError('Unexpected final pointer sentinel')
    source_words={int(r['table_file_offset'],16) for r in records}
    parts=[];descriptions=[];approved_simple=approved_complex=0
    old_bytes=0;new_bytes=0
    for i,(rec,row) in enumerate(zip(records,rows[:479])):
        at=int(rec['text_file_offset'],16);old=source[at:at+rec['length_bytes']]
        if (row['id']!=f'B6-{i:03d}' or row['bank']!='6' or int(row['index'])!=i or
            int(row['ptr_at'],16)!=int(rec['table_file_offset'],16) or
            int(row['text_at'],16)!=at or int(row['allocated'])!=len(old) or
            row['original_sha256']!=hashlib.sha256(old).hexdigest() or
            row['raw_hex']!=old.hex()):
            raise ValueError(f'Altered original TSV metadata at B6-{i:03d}')
        if len(old)<3 or old[-1]!=0 or b'\x00' in old[2:-1]:
            raise ValueError(f'Unexpected record termination at B6-{i:03d}')
        if row['status'] not in ('approved','draft','unreviewed'):
            raise ValueError('Unsupported translation state')
        if row['status']=='approved':
            # Carry speaker/metadata bytes unmodified; never reinterpret them.
            try:
                current=encode_preserving_header(old,row['english'],
                    allow_complex_header=allow_complex_header)
            except ValueError as e:
                raise ValueError(f'B6-{i:03d}: {e}') from e
            if old[:2]==SIMPLE:approved_simple+=1
            else:approved_complex+=1
        else:
            current=old
        if not current or current[-1]!=0 or b'\x00' in current[2:-1]:
            raise ValueError(f'B6-{i:03d}: invalid built record')
        parts.append(current);old_bytes+=len(old);new_bytes+=len(current)
        descriptions.append((i,int(rec['table_file_offset'],16),int(rec['cpu_pointer'],16),old[:2]))
    capacity=BANK6_END-BANK6_START
    if old_bytes!=capacity:raise AssertionError('Original string span mismatch')
    delta=new_bytes-capacity
    plan={
        'source_sha256':SOURCE_SHA,'records':479,
        'approved_simple':approved_simple,'approved_complex':approved_complex,
        'original_capacity_bytes':capacity,'repacked_bytes':new_bytes,
        'net_growth_bytes':delta,'available_padding_bytes':max(0,capacity-new_bytes),
        'overflow_bytes':max(0,delta),'fits_existing_bank':new_bytes<=capacity,
        'external_banks_allocated':0,'rom_expansion_performed':False,
        'runtime_references_verified':False,
        'note':'Only indexed Bank6 pointers can be checked offline; runtime references outside this table remain unverified.'
    }
    if new_bytes>capacity:
        return None,plan
    modified=bytearray(baseline)
    packed=pack_original_window(parts,capacity)
    if packed is None:raise AssertionError('Planner/build disagreement')
    modified[BANK6_START:BANK6_END]=packed
    cursor=BANK6_START; moved=[]
    for raw,(i,pointer_at,old_cpu,metadata) in zip(parts,descriptions):
        cpu=0x8000+(cursor-BANK6_TABLE)
        if not 0x8000<=cpu<0xC000:raise AssertionError('Relocation escaped mapped bank')
        struct.pack_into('<H',modified,pointer_at,cpu)
        if old_cpu!=cpu:moved.append({'record':i,'old_cpu':f'{old_cpu:04X}','new_cpu':f'{cpu:04X}'})
        if modified[cursor:cursor+2]!=metadata:raise AssertionError('Lost metadata bytes')
        cursor+=len(raw)
    if cursor!=BANK6_START+new_bytes:raise AssertionError('Packing position mismatch')
    # Preserve the source's reserved end pointer and each FFFF group delimiter.
    for at in range(BANK6_TABLE,0x18412,2):
        old=struct.unpack_from('<H',source,at)[0]
        if at not in source_words and struct.unpack_from('<H',modified,at)[0]!=old:
            raise AssertionError(f'Changed pointer group delimiter at {at:05X}')
    if modified[BANK6_TABLE:BANK6_TABLE+2]!=source[BANK6_TABLE:BANK6_TABLE+2]:
        raise AssertionError('Modified bank6 end pointer sentinel')
    allowed=set(range(BANK6_START,BANK6_END))
    allowed.update(x for at in source_words for x in (at,at+1))
    if any(i not in allowed for i,(before,after) in enumerate(zip(baseline,modified)) if before!=after):
        raise AssertionError('Unexpected patch change outside Bank6 data/pointer table')
    plan['moved_indexed_pointers']=len(moved)
    plan['moved_pointer_examples']=moved[:12]
    return bytes(modified),plan


def inject(source:bytes, rows:list[dict], *, allow_complex_header=False):
    # Create the same cumulative v1.7/approved Bank8 state as v1.8 while
    # withholding Bank6 entries for this engine's guarded global packing.
    prepared=[row.copy() for row in rows]
    for row in prepared[:479]:
        if row['status']=='approved':row['status']='draft'
    base_patch,_,base_report=v18.inject(source,prepared)
    baseline=v18.v16.apply_ips(source,base_patch)
    compiled,plan=compile_bank6(source,baseline,rows,allow_complex_header=allow_complex_header)
    if compiled is None:raise ValueError(f'Bank6 full-bank overflow: need {plan["overflow_bytes"]} additional bytes')
    forward=v18.diff_ips(source,compiled)
    undo=v18.diff_ips(compiled,source)
    if v18.v16.apply_ips(source,forward)!=compiled or v18.v16.apply_ips(compiled,undo)!=source:
        raise AssertionError('Exact reversible IPS check failed')
    if compiled[:16]!=source[:16] or len(compiled)!=len(source):
        raise AssertionError('ROM structure changed')
    return forward,undo,{**plan,'bank8_approved':base_report.get('approved_bank8'),
        'patched_sha256':hashlib.sha256(compiled).hexdigest(),
        'forward_ips_bytes':len(forward),'rollback_exact':True,
        'fceux_verified':False,'experimental_complex_header':allow_complex_header}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    choices=p.add_subparsers(dest='command',required=True)
    for command in ('plan','build'):
        q=choices.add_parser(command)
        q.add_argument('source',type=Path)
        q.add_argument('tsv',type=Path)
        q.add_argument('--allow-complex-header',action='store_true')
        q.add_argument('--out',type=Path,default=Path('work/v20'))
    a=p.parse_args(argv)
    source=read_source(a.source)
    rows=v18.load_edited(source,a.tsv)
    if a.command=='plan':
        baseline=source
        _,report=compile_bank6(source,baseline,rows,allow_complex_header=a.allow_complex_header)
    else:
        fwd,back,report=inject(source,rows,allow_complex_header=a.allow_complex_header)
        a.out.mkdir(parents=True,exist_ok=True)
        (a.out/'Square_Tom_Sawyer_Bank6_Repoint_v20.ips').write_bytes(fwd)
        (a.out/'Square_Tom_Sawyer_Bank6_Repoint_v20_ROLLBACK_PRIVATE.ips').write_bytes(back)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
