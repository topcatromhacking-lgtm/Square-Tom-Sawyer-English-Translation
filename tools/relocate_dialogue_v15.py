#!/usr/bin/env python3
"""v1.5 bounded dialogue repacker; structural proof, NOT a release patch.

Relocates only a contiguous window of indexed entries in ONE source-bank group.
Rejects overflow, invalid ROM identity, missing terminators and cross-bank
allocations. Unknown non-pointer runtime references still require game testing.
"""
from __future__ import annotations
import hashlib
import struct
from dataclasses import dataclass
from analyze_rom import get_record_map

SHA256='ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb'
BANK_START=0x18010
BANK_LIMIT=0x1C010

@dataclass(frozen=True)
class RepackResult:
    rom: bytes
    start_offset: int
    end_offset: int
    changes: tuple[tuple[int,int,int],...]
    used_bytes: int
    capacity_bytes: int

def repack_window(original:bytes,first:int,last:int,replacements:dict[int,bytes],
                  *,require_pointer_move:bool=False)->RepackResult:
    if hashlib.sha256(original).hexdigest()!=SHA256:
        raise ValueError('Must start with exact clean Japanese ROM')
    records,_=get_record_map(original)
    if (not isinstance(first,int) or not isinstance(last,int) or first<0 or
            last<first or last>=len(records)):
        raise ValueError('Invalid record range')
    block=records[first:last+1]
    if len({x['group'] for x in block})!=1:
        raise ValueError('Window cannot cross a pointer-table group boundary')
    if not replacements or any(not isinstance(k,int) or k<first or k>last for k in replacements):
        raise ValueError('Replacement records must be entirely within window')
    start=int(block[0]['text_file_offset'],16)
    end=start+sum(x['length_bytes'] for x in block)
    if not BANK_START<=start<end<=BANK_LIMIT:raise ValueError('Invalid bank-6 allocation')
    capacity=end-start
    chunks=[]
    offsets=[]
    cursor=start
    for rec in block:
        index=rec['global_index']
        if index in replacements:
            raw=replacements[index]
            if not isinstance(raw,bytes) or not raw or raw[-1]!=0:
                raise ValueError('Each replacement must be bytes ending in 00')
            if len(raw)>0x4000:raise ValueError('Implausible encoded record')
        else:
            at=int(rec['text_file_offset'],16)
            raw=original[at:at+rec['length_bytes']]
        offsets.append(cursor)
        cursor+=len(raw)
        chunks.append(raw)
    used=cursor-start
    if used>capacity:
        raise ValueError(f'Window overflow: {used} encoded bytes exceed {capacity} allocated; need {used-capacity} more')
    patched=bytearray(original)
    patched[start:end]=b''.join(chunks)+bytes(capacity-used)
    moved=[]
    for rec,loc in zip(block,offsets):
        ptr=0x8000+(loc-BANK_START)
        if not 0x8000<=ptr<0xC000:raise ValueError('Pointer crosses PRG bank')
        at=int(rec['table_file_offset'],16)
        old=struct.unpack_from('<H',original,at)[0]
        if old!=ptr:moved.append((rec['global_index'],old,ptr))
        struct.pack_into('<H',patched,at,ptr)
    if require_pointer_move and not moved:raise ValueError('No pointers actually relocated')
    for ix,loc in enumerate(offsets):
        following=offsets[ix+1] if ix+1<len(offsets) else end
        if patched[following-1]!=0:raise AssertionError('Lost terminal 00 after packing')
        if loc>=following:raise AssertionError('Empty allocation after pointer relocation')
    allowed=set(range(start,end))
    for rec in block:
        at=int(rec['table_file_offset'],16)
        allowed.update((at,at+1))
    if any(i not in allowed for i,(a,b) in enumerate(zip(original,patched)) if a!=b):
        raise AssertionError('Unexpected modification outside selected data/pointers')
    return RepackResult(bytes(patched),start,end,tuple(moved),used,capacity)
