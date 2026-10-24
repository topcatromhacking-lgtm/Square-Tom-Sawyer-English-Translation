#!/usr/bin/env python3
"""v1.8 source-pinned indexed script dump / approved translation injector.

The complete extraction covers the 479 pointer-indexed bank-6 records and 41
pointer-indexed bank-8 events. It does NOT claim to cover game menus, arbitrary
battle strings, dictionaries or other unindexed text.

Command examples:
  python tools/script_pipeline_v18.py dump ORIGINAL.zip --out work/script/master_PRIVATE.tsv --seed-opening
  python tools/script_pipeline_v18.py report ORIGINAL.zip work/script/master_PRIVATE.tsv
  python tools/script_pipeline_v18.py build ORIGINAL.zip work/script/master_PRIVATE.tsv --out work/v18

All full script exports and edited translations are private; never commit them.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,struct
from pathlib import Path
from collections import Counter
from analyze_rom import get_record_map,read_source
from english_codec_v15 import encode
import build_opening_v16 as v16
import build_overworld_menu_v17 as v17

SHA='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
FIELDS=('id','bank','index','group','ptr_at','text_at','allocated','original_sha256',
        'raw_hex','japanese_partial','english','status','notes')
BANK8_TABLE=0x2124D
BANK8_BASE=0x20010
BANK8_COUNT=41
BANK8_DATA_END=0x2177C
BANK6_FIRST=0x18812
BANK6_END=0x1C007

# Known decoded controls are represented visibly in private, not re-encoded
# wholesale: the original corpus can include dictionary/prefix conventions.
def partial_japanese(raw:bytes,glyphs:dict[int,str])->str:
    out=[]
    for b in raw:
        if b==0:out.append('[END]')
        elif b==1:out.append('[NL]')
        else:out.append(glyphs.get(b,'<%02X>'%b))
    return ''.join(out)

def load_glyphs(filename:Path|None)->dict[int,str]:
    result={}
    if filename is None:return result
    for line in filename.read_text(encoding='utf8').splitlines():
        if not line or line.lstrip().startswith('#'):continue
        b,letter=line.split('=',1)
        if len(letter)!=1:raise ValueError('Invalid source glyph dictionary')
        result[int(b,16)]=letter
    return result

def inventory(rom:bytes,glyphs:dict[int,str]|None=None)->list[dict]:
    if hashlib.sha256(rom).hexdigest()!=SHA:raise ValueError('Expected exact Japanese original ROM')
    glyphs=glyphs or {}
    source_records,meta=get_record_map(rom)
    if len(source_records)!=479 or meta['group_counts']!=[251,35,123,70]:
        raise AssertionError('Unexpected bank-6 pointer corpus')
    rows=[]
    for rec in source_records:
        at=int(rec['text_file_offset'],16)
        raw=rom[at:at+rec['length_bytes']]
        rows.append(dict(id='B6-%03d'%rec['global_index'],bank='6',index=str(rec['global_index']),
            group=str(rec['group']),ptr_at=rec['table_file_offset'],
            text_at=rec['text_file_offset'],allocated=str(len(raw)),
            original_sha256=hashlib.sha256(raw).hexdigest(),raw_hex=raw.hex(),
            japanese_partial=partial_japanese(raw,glyphs),english='',status='unreviewed',notes=''))
    pointers=[]
    for i in range(BANK8_COUNT):
        at=BANK8_TABLE+i*2
        cpu=struct.unpack_from('<H',rom,at)[0]
        loc=BANK8_BASE+cpu-0x8000
        pointers.append((at,loc))
    if pointers[0][1]!=v16.TEXT_START or pointers[12][1]!=v16.TEXT_END:
        raise ValueError('Changed event table boundaries')
    if not all(a[1]<b[1] for a,b in zip(pointers,pointers[1:])):
        raise ValueError('Event pointers not monotonically increasing')
    if pointers[-1][1]!=0x2176A or rom[BANK8_DATA_END-1]!=0 or rom[BANK8_DATA_END]!=0x20:
        raise ValueError('Unverified final event-record boundary')
    for i,(pat,at) in enumerate(pointers):
        end=pointers[i+1][1] if i+1<BANK8_COUNT else BANK8_DATA_END
        raw=rom[at:end]
        if not raw or raw[-1]!=0:
            raise ValueError(f'Event record {i} not terminated')
        rows.append(dict(id='B8-%02d'%i,bank='8',index=str(i),group='event',
            ptr_at='0x%05X'%pat,text_at='0x%05X'%at,allocated=str(len(raw)),
            original_sha256=hashlib.sha256(raw).hexdigest(),raw_hex=raw.hex(),
            japanese_partial=partial_japanese(raw,glyphs),english='',status='unreviewed',notes=''))
    if len(rows)!=520:raise AssertionError('Expected 479 + 41 records')
    return rows

SCRIPT_PTR_RE=re.compile(r'^//POINTER #\d+ @ \$([0-9A-Fa-f]+) - STRING #\d+ @ \$([0-9A-Fa-f]+)',re.M)

def references(path:Path)->list[dict]:
    text=path.read_text(encoding='utf-8-sig')
    matches=list(SCRIPT_PTR_RE.finditer(text));out=[]
    for k,match in enumerate(matches):
        segment=text[match.end():matches[k+1].start() if k+1<len(matches) else len(text)]
        end=re.search(r'\[ED\]',segment,re.I)
        translated=' '.join(line.strip() for line in segment[end.end():].splitlines() if line.strip()) if end else ''
        if translated.startswith('^(('):translated=''
        out.append(dict(ptr=int(match[1],16),text=int(match[2],16),english=translated,filename=path.name))
    return out

def merge(rows:list[dict],external:list[dict])->tuple[list[dict],list[dict]]:
    from collections import defaultdict
    by_location=defaultdict(list)
    by_ptr=defaultdict(list)
    for x in external:
        by_location[x['ptr'],x['text']].append(x)
        by_ptr[x['ptr']].append(x)
    conflicts=[];matched=set()
    for row in rows:
        p,t=int(row['ptr_at'],16),int(row['text_at'],16)
        entries=by_location.get((p,t),[])
        if len(entries)==1:
            ref=entries[0];matched.add(id(ref))
            row['english']=ref['english'];row['notes']='External draft: '+ref['filename']
            row['status']='draft' if ref['english'] else 'unreviewed'
        elif len(entries)>1:
            conflicts.append({'ptr':'%05X'%p,'text':'%05X'%t,'reason':'multiple external candidates'})
        elif p in by_ptr:
            conflicts.append({'ptr':'%05X'%p,'text':'%05X'%t,'reason':'external text offset differs'})
    for x in external:
        if id(x) not in matched:
            reason='GROUP_DELIMITER_FFFF' if x['ptr'] in (0x1820A,0x18252) else 'unmatched or duplicate pointer/text'
            conflicts.append({'ptr':'%05X'%x['ptr'],'text':'%05X'%x['text'],'reason':reason})
    return rows,conflicts

def dump(rom:bytes,out:Path,scripts:list[Path],seed_opening:bool,glyph_map:Path|None)->dict:
    rows=inventory(rom,load_glyphs(glyph_map))
    conflicts=[]
    if scripts:
        rows,conflicts=merge(rows,[x for p in scripts for x in references(p)])
    if seed_opening:
        for i,text in enumerate(v16.TEXTS):
            row=rows[479+i];assert row['id']=='B8-%02d'%i
            row['english']=text.replace('\n','\\n')
            row['status']='approved'
            row['notes']='Verified v1.6 opening, replaces any external draft'
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,delimiter='\t',fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
    if conflicts:
        out.with_name('unmatched_references_PRIVATE.json').write_text(json.dumps(conflicts,indent=2)+'\n',encoding='utf-8')
    return {'total_indexed':len(rows),'bank6':479,'bank8':41,'external_references':sum(len(references(p)) for p in scripts),
            'reference_warnings':len(conflicts),'translated_candidates':sum(bool(x['english']) for x in rows),
            'approved':sum(x['status']=='approved' for x in rows),'private_tsv':str(out)}

def load_edited(rom:bytes,filename:Path)->list[dict]:
    expected=inventory(rom)
    with filename.open('r',encoding='utf-8-sig',newline='') as f:
        rdr=csv.DictReader(f,delimiter='\t')
        if set(FIELDS)-set(rdr.fieldnames or []):raise ValueError('Missing TSV columns')
        found=list(rdr)
    if len(found)!=len(expected):raise ValueError('TSV records missing or added')
    for standard,row in zip(expected,found):
        for field in ('id','bank','index','group','ptr_at','text_at','allocated','original_sha256','raw_hex'):
            if row[field]!=standard[field]:raise ValueError(f'Original field changed: {standard["id"]}/{field}')
        if row['status'] not in ('unreviewed','draft','approved'):
            raise ValueError('Unknown record status')
    return found

def analyze(rom:bytes,rows:list[dict])->dict:
    approved=[r for r in rows if r['status']=='approved']
    lower_overflows=[];errors=[]
    counts=Counter()
    for r in rows:
        if not r['english']:continue
        if r['status']=='approved':
            try:
                encoded=encode(r['english'].replace('\\n','\n'),
                               maximum_lines=3 if r['id']=='B8-00' else 2,
                               maximum_chars_per_line=20).data
                if len(encoded)>int(r['allocated']):lower_overflows.append(r['id'])
            except ValueError as exc:errors.append({'id':r['id'],'error':str(exc)})
        counts[r['bank']]+=1
    return {'total_records':len(rows),'candidate_by_bank':dict(counts),'approved_count':len(approved),
            'approved_bank6':sum(r['bank']=='6' for r in approved),
            'approved_bank8':sum(r['bank']=='8' for r in approved),
            'individually_overflowing_approved':len(lower_overflows),'invalid_approved':errors[:30],
            'ready_for_runtime_pack':not errors and not any(r['bank']=='6' for r in approved)}

def diff_ips(source:bytes,modified:bytes)->bytes:
    if len(source)!=len(modified):raise ValueError('ROM expansion unsupported')
    edits=[];i=0
    while i<len(source):
        if source[i]==modified[i]:i+=1;continue
        start=i
        while i<len(source) and source[i]!=modified[i] and i-start<65535:i+=1
        edits.append((start,modified[start:i]))
    return v16.make_ips(edits)

def inject(rom:bytes,rows:list[dict])->tuple[bytes,bytes,dict]:
    stats=analyze(rom,rows)
    if stats['invalid_approved']:raise ValueError('Approved entries with invalid encoding: '+str(stats['invalid_approved'][:2]))
    if stats['approved_bank6']:
        raise ValueError('Bank 6 has dictionary/prefix metadata not yet classified: injection is disabled, but dump/report work')
    # Start from user-verified cumulative v1.7 and preserve its font/menus.
    baseline,_,_=v17.build(rom)
    modified=bytearray(v16.apply_ips(rom,baseline))
    event=rows[479:]
    assert len(event)==41
    # Packing uses two independent anchored windows: first 12 (proven v1.6),
    # and later events 12..40 (not yet FCEUX-verified, but structurally gated).
    for lo,hi,beg,end in ((0,12,0x2129F,0x213EC),(12,41,0x213EC,BANK8_DATA_END)):
        batch=event[lo:hi]
        if not any(x['status']=='approved' for x in batch):continue
        parts=[]
        if lo==0 and any(x['status']!='approved' for x in batch):
            raise ValueError('The first 12 verified intro records must be approved together')
        for row in batch:
            if row['status']=='approved':
                text=row['english'].replace('\\n','\n')
                raw=encode(text,maximum_lines=3 if row['id']=='B8-00' else 2,
                           maximum_chars_per_line=20).data
            else:
                raw=bytes.fromhex(row['raw_hex'])
            if raw[-1]!=0 or not raw:raise ValueError('Broken encoded record')
            parts.append(raw)
        used=sum(map(len,parts));capacity=end-beg
        if used>capacity:raise ValueError(f'Bank 8 window {lo}-{hi} overflows by {used-capacity} bytes; relocation required')
        cursor=beg
        for row,raw in zip(batch,parts):
            ptr_at=int(row['ptr_at'],16)
            ptr=0x8000+cursor-BANK8_BASE
            if not 0x8000<=ptr<0xC000:raise AssertionError('Pointer escaped bank')
            struct.pack_into('<H',modified,ptr_at,ptr)
            cursor+=len(raw)
        modified[beg:end]=b''.join(parts)+bytes(capacity-used)
    out=bytes(modified)
    if out[0x21265:0x2129F]!=rom[0x21265:0x2129F]:
        # This span holds OTHER pointers, and is allowed to change only if
        # the later window actually acquired approvals. All string pointers
        # were recomputed for those cases, not arbitrary code.
        if not any(r['status']=='approved' for r in event[12:]):
            raise AssertionError('Unexpected later pointer edits')
    if out[:16]!=rom[:16] or len(out)!=len(rom):raise AssertionError('ROM structure changed')
    fwd=diff_ips(rom,out);undo=diff_ips(out,rom)
    if v16.apply_ips(rom,fwd)!=out or v16.apply_ips(out,undo)!=rom:
        raise AssertionError('Forward/rollback mismatch')
    return fwd,undo,{**stats,'source_sha256':SHA,'patched_sha256':hashlib.sha256(out).hexdigest(),
        'forward_ips_bytes':len(fwd),'exact_rollback':True,'requires_fceux':True,
        'scope':'Bank 8 indexed events only; bank 6 insertion intentionally blocked'}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='mode',required=True)
    d=commands.add_parser('dump');d.add_argument('source',type=Path);d.add_argument('--out',type=Path,default=Path('work/script/master_PRIVATE.tsv'))
    d.add_argument('--script',action='append',type=Path,default=[]);d.add_argument('--seed-opening',action='store_true')
    d.add_argument('--glyph-map',type=Path)
    q=commands.add_parser('report');q.add_argument('source',type=Path);q.add_argument('tsv',type=Path)
    b=commands.add_parser('build');b.add_argument('source',type=Path);b.add_argument('tsv',type=Path)
    b.add_argument('--out',type=Path,default=Path('work/v18'))
    args=parser.parse_args(argv)
    rom=read_source(args.source)
    if args.mode=='dump':report=dump(rom,args.out,args.script,args.seed_opening,args.glyph_map)
    elif args.mode=='report':report=analyze(rom,load_edited(rom,args.tsv))
    else:
        edited=load_edited(rom,args.tsv)
        forward,rollback,report=inject(rom,edited)
        args.out.mkdir(parents=True,exist_ok=True)
        (args.out/'Square_Tom_Sawyer_Script_Injection_v18.ips').write_bytes(forward)
        # Source-derived rollback bytes remain private local output only.
        (args.out/'Square_Tom_Sawyer_Script_Injection_v18_ROLLBACK_PRIVATE.ips').write_bytes(rollback)
        (args.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
