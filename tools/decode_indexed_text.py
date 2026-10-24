#!/usr/bin/env python3
"""Partial Japanese text decoder for the exact original Square no Tom Sawyer ROM.

Unknown codes are <XX>; no English translation or control-code interpretation.
Output contains source dialogue and MUST remain in gitignored work/.
"""
import argparse
import json
from pathlib import Path
from collections import Counter
from analyze_rom import read_source, get_record_map

MAP_PATH = Path(__file__).resolve().parents[1]/"docs/glyph-map-v01.tbl"

def load_map(path=MAP_PATH):
    mapping={}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"): continue
        code,glyph=line.split("=",1)
        if len(glyph)!=1: raise ValueError("Not a single glyph: "+line)
        n=int(code,16)
        if n in mapping: raise ValueError("Duplicate glyph code: "+code)
        mapping[n]=glyph
    return mapping

def decode_raw(data,mapping):
    return "".join(mapping.get(b,f"<{b:02X}>") for b in data)

def report(data,mapping=None):
    mapping=load_map() if mapping is None else mapping
    records,_=get_record_map(data)
    total=matched=0
    unknown=Counter()
    decoded=[]
    for rec in records:
        offset=int(rec["text_file_offset"],16)
        blob=data[offset:offset+rec["length_bytes"]]
        for b in blob:
            if b in (0,1):continue
            total+=1
            if b in mapping:matched+=1
            else:unknown[b]+=1
        decoded.append({"index":rec["global_index"],"group":rec["group"],
                        "pointer":rec["cpu_pointer"],"private_text":decode_raw(blob,mapping)})
    return {"indexed_records":len(records),"mapped_character_codes":len(mapping),
            "non_00_01_bytes":total,"mapped_bytes":matched,
            "fraction":matched/total if total else 0,
            "unknown_codes":[{"hex":f"{k:02X}","count":v} for k,v in unknown.most_common()],
            "caution":"Partial code table; 00/01 control meanings unknown. PRIVATE source-derived text.",
            "private_decoded_records":decoded}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom",type=Path)
    ap.add_argument("--out",type=Path,default=Path("work/decoded-private.json"))
    opts=ap.parse_args()
    result=report(read_source(opts.rom))
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{result['indexed_records']} records; {result['mapped_character_codes']} glyphs;"
          f" {result['fraction']:.1%} mapped non-00/01 bytes. PRIVATE output at {opts.out}")

if __name__=="__main__": main()
