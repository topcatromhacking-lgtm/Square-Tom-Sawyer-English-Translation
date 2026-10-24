#!/usr/bin/env python3
"""Verified, read-only static decoder for Square no Tom Sawyer 6502 text code."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

SOURCE_SHA256 = "ee7b3598706305b0714f10d396dd882578fd54cfda85bcd4fa5bf7fbb2f8dacb"

def read_original(path):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".nes")]
            if len(names) != 1: raise ValueError("Expected exactly one .nes file")
            data = z.read(names[0])
    elif path.suffix.lower() == ".nes":
        data = path.read_bytes()
    else:
        raise ValueError("Expected original .nes or ZIP")
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Wrong ROM or patched ROM")
    return data

def rom_offset(bank, cpu):
    if bank == 15 and 0xC000 <= cpu < 0x10000:
        return 16 + 15 * 0x4000 + cpu - 0xC000
    if 0 <= bank < 15 and 0x8000 <= cpu < 0xC000:
        return 16 + bank * 0x4000 + cpu - 0x8000
    raise ValueError("Invalid bank or CPU address")

SIGNATURES = (
    (8, 0x8391, "b122", "LDA ($22),Y: trace callback PC 8393 is next instruction"),
    (8, 0x8393, "f024c901", "BEQ end; CMP #01 for linebreak"),
    (8, 0x83C0, "20b4c0", "JSR $C0B4 decoder veneer"),
    (15, 0xC0B4, "4c50ee", "JMP $EE50 fixed converter"),
    (15, 0xEE50, "c909b001602063ee4898186970a86818697060", "Normal text tile mapping"),
    (15, 0xEE63, "a08fc98fd00160a08fc990b00160a00ec99fb00438e96360", "High-code mapping first branch"),
    (15, 0xEE7B, "c9b0b00438e95e60c9bfb00438e94d60c9c4b00438e94860a00fc9c9b00438e9836038e95260", "High-code mapping remaining branches"),
)

def verify(rom):
    result = []
    for bank, cpu, expected, comment in SIGNATURES:
        offset = rom_offset(bank, cpu)
        sample = rom[offset:offset + len(expected)//2]
        if sample.hex() != expected:
            raise ValueError("Decoder changed at bank %d $%04X" % (bank,cpu))
        result.append({"bank":bank,"cpu":"%04X" % cpu,"file_offset":"%05X" % offset,
                       "verified":True,"meaning":comment})
    return result

def convert(code):
    """Model of instructions $EE50-$EEA0. A: lower tile, Y: upper tile."""
    if not isinstance(code,int) or not 0 <= code < 256:
        raise ValueError("Input must be one byte")
    if code < 9:
        return {"input":code,"kind":"early-return","A":code,"Y":None}
    if code <= 0x8F:
        base, upper, kind = code, 0x8F, ("space" if code == 0x8F else "normal")
    elif code < 0x9F:
        base, upper, kind = code-0x63, 0x0E, "dakuten"
    elif code < 0xB0:
        base, upper, kind = code-0x5E, 0x0E, "dakuten"
    elif code < 0xBF:
        base, upper, kind = code-0x4D, 0x0E, "dakuten"
    elif code < 0xC4:
        base, upper, kind = code-0x48, 0x0E, "dakuten"
    elif code < 0xC9:
        base, upper, kind = code-0x83, 0x0F, "handakuten"
    else:
        base, upper, kind = code-0x52, 0x0F, "handakuten"
    return {"input":code,"kind":kind,"A":(base+0x70)&255,"Y":(upper+0x70)&255}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom",type=Path)
    parser.add_argument("--out",type=Path,default=Path("work/decoder_v08.json"))
    args=parser.parse_args()
    rom=read_original(args.rom)
    data={"source_sha256":SOURCE_SHA256,"instruction_checks":verify(rom),
          "conversion_table":[convert(i) for i in range(256)],
          "runtime_verified":False,
          "warning":"Tile mapping is statically verified; PPU bitmap loading not yet traced."}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2)+"\n",encoding="utf8")
    for i in [0x70,0x8e,0x8f,0x9b,0xa4,0xa5]:
        print("%02X -> %s"%(i,convert(i)))
    print("PASS:",len(data["instruction_checks"]),"6502 ROM signatures")

if __name__=="__main__":main()
