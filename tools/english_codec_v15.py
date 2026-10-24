#!/usr/bin/env python3
"""v1.5: canonical one-byte English encoder, without ROM changes.

A-Z codes 6E-87: confirmed from historic Translation 2.0 bitmaps.
Numerals 10-19: confirmed by the original Japanese intro ("1855").
LF=01, end=00, space=8F. Apostrophe 88 and question 8D were verified\nfrom historical Translation 2.0 bitmaps. Other punctuation is provisional pending
FCEUX verification; no silent wrapping or lossy glyph substitution.
"""
from __future__ import annotations
from dataclasses import dataclass

ALPHABET={chr(ord('A')+i):0x6E+i for i in range(26)}
DIGITS={str(i):0x10+i for i in range(10)}
PUNCTUATION={'?':0x8D,'-':0x89,',':0x8A,'.':0x8B,'!':0x8C,"'":0x88}
SPACE,NEWLINE,TERMINATOR=0x8F,0x01,0x00
CHAR_TO_BYTE={**ALPHABET,**DIGITS,**PUNCTUATION,' ':SPACE}
BYTE_TO_CHAR={v:k for k,v in CHAR_TO_BYTE.items()}

@dataclass(frozen=True)
class Encoded:
    data: bytes
    lines: tuple[str,...]

def encode(text:str,*,terminate:bool=True,maximum_lines:int|None=None,
           maximum_chars_per_line:int|None=None)->Encoded:
    if not isinstance(text,str):raise TypeError('Text must be str')
    if '\r' in text or '\t' in text:raise ValueError('Use LF and spaces, not CR or tabs')
    lines=tuple(text.split('\n'))
    if not text or any(not line for line in lines):raise ValueError('Empty text/line is not permitted')
    if maximum_lines is not None and len(lines)>maximum_lines:raise ValueError('Too many lines')
    if maximum_chars_per_line is not None and any(len(line)>maximum_chars_per_line for line in lines):
        raise ValueError('Exceeds chosen text-window width')
    out=[]
    for line_no,line in enumerate(lines):
        if line_no:out.append(NEWLINE)
        for col,char in enumerate(line):
            c=char.upper() if 'a'<=char<='z' else char
            if c not in CHAR_TO_BYTE:
                raise ValueError(f'Unsupported glyph {char!r} on line {line_no+1}, column {col+1}')
            out.append(CHAR_TO_BYTE[c])
    if terminate:out.append(TERMINATOR)
    return Encoded(bytes(out),lines)

def decode(data:bytes)->str:
    out=[]
    for i,byte in enumerate(data):
        if byte==TERMINATOR:
            if i!=len(data)-1:raise ValueError('Trailing bytes after terminator')
            return ''.join(out)
        if byte==NEWLINE:out.append('\n')
        elif byte in BYTE_TO_CHAR:out.append(BYTE_TO_CHAR[byte])
        else:raise ValueError(f'Unknown English byte 0x{byte:02X} at offset {i}')
    return ''.join(out)
