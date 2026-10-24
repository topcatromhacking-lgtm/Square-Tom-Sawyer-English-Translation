#!/usr/bin/env python3
"""v1.1 reversible full-uppercase Latin introductory patch (DIAGNOSTIC ONLY).

Uses the verified 8-byte 1bpp font table discovered in v0.5. Overwrites 37
populated Japanese glyphs globally. Does NOT provide bilingual font switching.
Original 262160-byte iNES ROM only; no ROM redistributed.
"""
from pathlib import Path
import hashlib, json
from analyze_rom import read_source
from make_intro_probe import ips_make,ips_apply
SOURCE="ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb"
PATCHED="a76bb5678a183ba2b36e4fb27ac90b4597c08e850be91db9260dd050e0fa940e"
FONT_BASE=0x17710
ORDER="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,"
GLYPH_CODES={c:(0x44 if c=="," else 0x20+i) for i,c in enumerate(ORDER)}
HEX_GLYPHS={
"A":"003844447c444444","B":"0078444478444478","C":"003c40404040403c",
"D":"0078444444444478","E":"007c40407840407c","F":"007c404078404040",
"G":"003c40405c444438","H":"004444447c444444","I":"007c10101010107c",
"J":"001c080808484830","K":"0044485060504844","L":"004040404040407c",
"M":"00446c5454444444","N":"004464544c444444","O":"0038444444444438",
"P":"0078444478404040","Q":"0038444444544834","R":"0078444478504844",
"S":"003c404038040478","T":"007c101010101010","U":"0044444444444438",
"V":"0044444444442810","W":"0044444454546c44","X":"0044442810284444",
"Y":"0044442810101010","Z":"007c04081020407c","0":"0038444c54644438",
"1":"0010301010101038","2":"003844040810207c","3":"0078040438040478",
"4":"004444447c040404","5":"007c404078040478","6":"0038404078444438",
"7":"007c040810202020","8":"0038444438444438","9":"003844443c040438",
",":"0000000000001810",
}
LINES=(
(0x2129F,"AMERICA",bytes.fromhex("8F 5E 7F 85 63 90 8C 33 26 2A 31 2F")),
(0x212AC,"MISSOURI",bytes.fromhex("8F 8F 7D B7 85 0B 33 26 2A")),
(0x212B6,"ONE NIGHT, 1855",bytes.fromhex("11 18 15 15 3F 55 40 8F 28 50 9F 55 24 24 24")),
)
def make(rom):
    if len(rom)!=262160 or hashlib.sha256(rom).hexdigest()!=SOURCE:
        raise ValueError("Wrong source ROM. Use the clean Japanese image.")
    if set(HEX_GLYPHS)!=set(GLYPH_CODES):
        raise AssertionError("Font incomplete")
    edits=[];undo=[];updated=bytearray(rom)
    for c,code in sorted(GLYPH_CODES.items(),key=lambda x:x[1]):
        at=FONT_BASE+8*code
        new=bytes.fromhex(HEX_GLYPHS[c]);old=rom[at:at+8]
        assert len(new)==8 and new!=old
        edits.append((at,new));undo.append((at,old));updated[at:at+8]=new
    for ofs,english,original in LINES:
        if rom[ofs:ofs+len(original)]!=original:
            raise ValueError("Unrecognized original intro")
        if len(english)>len(original):raise ValueError("Text overflow")
        new=bytes(0x8F if c==" " else GLYPH_CODES[c] for c in english)
        new+=bytes([0x8F])*(len(original)-len(new))
        edits.append((ofs,new));undo.append((ofs,original))
        updated[ofs:ofs+len(original)]=new
    if [rom[0x212AB],rom[0x212B5],rom[0x212C5]]!=[1,1,0]:
        raise ValueError("Original line separators / terminator changed")
    updated=bytes(updated)
    fw=ips_make(sorted(edits));rv=ips_make(sorted(undo))
    assert ips_apply(rom,fw)==updated and ips_apply(updated,rv)==rom
    assert hashlib.sha256(updated).hexdigest()==PATCHED
    assert updated[:16]==rom[:16]
    assert [updated[0x212AB],updated[0x212B5],updated[0x212C5]]==[1,1,0]
    return fw,rv,{'source_sha256':SOURCE,'patched_sha256':PATCHED,'rollback_sha256':SOURCE,
        'font_glyphs':37,'lines':[line for _,line,_ in LINES],'ips_records':40,
        'emulator_verified':False,
        'warning':'Intro-only diagnostic: 37 Japanese glyph patterns globally overwritten; do not save. Not a bilingual English font.'}
def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom",type=Path);p.add_argument("--out",type=Path,default=Path("work/english-v11"))
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    fwd,rev,manifest=make(read_source(a.rom))
    (a.out/"Square_Tom_Sawyer_English_Intro_v11.ips").write_bytes(fwd)
    (a.out/"Square_Tom_Sawyer_English_Intro_v11_ROLLBACK.ips").write_bytes(rev)
    (a.out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()
