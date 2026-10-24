#!/usr/bin/env python3
"""Build a reversible intro TEST diagnostic IPS, never a complete ROM.

No emulator validation is claimed. Forward patch changes only eleven glyph
bytes in the first narrator line to katakana 'テスト' plus eight spaces.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from analyze_rom import read_source, get_record_map

POINTER_OFFSET=0x2124D
INTRO_START=0x2129F
EDIT_START=INTRO_START+1
ORIGINAL_LINE=bytes.fromhex("8F 5E 7F 85 63 90 8C 33 26 2A 31 2F 01")
NEW_INTERIOR=bytes([0x70,0x6A,0x71]+[0x8F]*8)
NEW_LINE=bytes([0x8F])+NEW_INTERIOR+bytes([0x01])

def apply_at_verified_offset(data):
    get_record_map(data)  # exact original ROM fingerprint
    cpu_ptr=struct.unpack_from("<H",data,POINTER_OFFSET)[0]
    if 16+8*0x4000+cpu_ptr-0x8000 != INTRO_START:
        raise ValueError("Intro pointer mismatch")
    if data[INTRO_START:INTRO_START+13]!=ORIGINAL_LINE:
        raise ValueError("Unexpected original intro text bytes")
    out=bytearray(data)
    out[EDIT_START:EDIT_START+11]=NEW_INTERIOR
    result=bytes(out)
    diffs=[i for i,(a,b) in enumerate(zip(data,result)) if a!=b]
    if not diffs or not set(diffs).issubset(set(range(EDIT_START,EDIT_START+11))):
        raise AssertionError("Modification escaped target line")
    if result[:16]!=data[:16] or result[POINTER_OFFSET:POINTER_OFFSET+2]!=data[POINTER_OFFSET:POINTER_OFFSET+2]:
        raise AssertionError("Header or pointer changed")
    if result[INTRO_START:INTRO_START+13]!=NEW_LINE:
        raise AssertionError("Diagnostic line mismatch")
    return result

def ips_make(records):
    out=bytearray(b"PATCH")
    previous=-1
    for off,data in records:
        if not (0<=off<0x454F46) or off<=previous or not (0<len(data)<=65535):
            raise ValueError("Invalid IPS record or order")
        out+=off.to_bytes(3,"big")+len(data).to_bytes(2,"big")+data
        previous=off+len(data)-1
    return bytes(out)+b"EOF"

def ips_apply(source,patch):
    if not patch.startswith(b"PATCH") or not patch.endswith(b"EOF"):
        raise ValueError("Malformed IPS container")
    result=bytearray(source)
    i=5
    while i<len(patch)-3:
        if i+5>len(patch)-3:raise ValueError("Truncated IPS header")
        offset=int.from_bytes(patch[i:i+3],"big")
        size=int.from_bytes(patch[i+3:i+5],"big")
        i+=5
        if size==0 or i+size>len(patch)-3 or offset+size>len(result):
            raise ValueError("Invalid IPS span")
        result[offset:offset+size]=patch[i:i+size]
        i+=size
    if i!=len(patch)-3:raise ValueError("IPS trailing data")
    return bytes(result)

def build(original):
    updated=apply_at_verified_offset(original)
    forward=ips_make([(EDIT_START,NEW_INTERIOR)])
    rollback=ips_make([(EDIT_START,ORIGINAL_LINE[1:-1])])
    assert ips_apply(original,forward)==updated
    assert ips_apply(updated,rollback)==original
    manifest={"format":"IPS","stage":"katakana TEST diagnostic; not English",
      "emulator_verified":False,"changed_offsets":[f"0x{i:05X}" for i,(a,b)
      in enumerate(zip(original,updated)) if a!=b],
      "expected_display":"テスト","source_sha256":hashlib.sha256(original).hexdigest(),
      "patched_sha256":hashlib.sha256(updated).hexdigest(),
      "rollback_sha256":hashlib.sha256(ips_apply(updated,rollback)).hexdigest(),
      "pointer_changed":False,"header_changed":False}
    return forward,rollback,manifest

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom",type=Path)
    ap.add_argument("--out",type=Path,default=Path("work/intro-probe"))
    args=ap.parse_args()
    a,b,manifest=build(read_source(args.rom))
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Square_Tom_Sawyer_Intro_TEST_v03.ips").write_bytes(a)
    (args.out/"Square_Tom_Sawyer_Intro_TEST_v03_ROLLBACK.ips").write_bytes(b)
    (args.out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("PASS: forward+rollback produce byte-identical original; emulator visual proof still pending")

if __name__=="__main__":main()
