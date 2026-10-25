#!/usr/bin/env python3
"""v25 hypothetical same-Bank6 text + phrase dictionary layout planner.

This is an allocation *model*, not a native NES codec. It assumes a future
separate dictionary-pointer lookup in CPU bank 6, an English-only token
namespace, and lossless encoded record/phrase byte streams. It cannot by itself
generate a ROM, assign tokens, or establish runtime decoder compatibility.
"""
from __future__ import annotations
from dataclasses import dataclass
import argparse,json

TEXT_START=0x18812
TEXT_END=0x1C007
BANK_START=0x18010
CAPACITY=TEXT_END-TEXT_START
RECORDS=479

@dataclass(frozen=True)
class Layout:
    record_start:int
    record_end:int
    dictionary_pointer_start:int
    dictionary_pointer_end:int
    phrase_start:int
    phrase_end:int
    padding_bytes:int

def plan(*,encoded_symbols:int, dictionary_phrase_data_bytes:int,
         tokens:int,records:int=RECORDS)->dict:
    """Count 2 prefix + 1 end per record; 2-byte table per phrase.

    dictionary_phrase_data_bytes is sum(len(phrase)+1) for each phrase.
    Explicit line/control bytes must ALREADY be counted in encoded_symbols.
    """
    if records!=479 or not 0<=tokens<=190 or encoded_symbols<0:
        raise ValueError('Invalid Bank6 record/token count')
    if dictionary_phrase_data_bytes<tokens*2:
        raise ValueError('Every phrase requires >=1 byte plus 1 terminator')
    record_used=encoded_symbols+3*records
    dictionary_pointer_bytes=tokens*2
    combined=record_used+dictionary_pointer_bytes+dictionary_phrase_data_bytes
    margin=CAPACITY-combined
    layout=None
    if margin>=0:
        a=TEXT_START
        b=a+record_used
        c=b+dictionary_pointer_bytes
        d=c+dictionary_phrase_data_bytes
        if d>TEXT_END:raise AssertionError('Model unexpectedly exceeded Bank6')
        def cpu(pos):return 0x8000+pos-BANK_START
        if not all(0x8000<=cpu(at)<0xC000 for at in (a,b,c,d-1)):
            raise ValueError('Layout escapes MMC1 bank6 CPU window')
        layout={'text_start_file':f'{a:05X}',
                'text_end_exclusive_file':f'{b:05X}',
                'dictionary_pointer_start_file':f'{b:05X}',
                'dictionary_pointer_start_cpu':f'{cpu(b):04X}',
                'phrase_data_start_file':f'{c:05X}',
                'phrase_data_start_cpu':f'{cpu(c):04X}',
                'phrase_data_end_exclusive_file':f'{d:05X}',
                'padding_bytes':margin}
    return {'model_only':True,'records':records,'tokens':tokens,
            'original_bank6_capacity':CAPACITY,
            'encoded_symbols':encoded_symbols,
            'record_structure_bytes':3*records,
            'record_bytes':record_used,
            'new_pointer_table_bytes':dictionary_pointer_bytes,
            'phrase_data_bytes':dictionary_phrase_data_bytes,
            'total_needed_bytes':combined,
            'margin_bytes':margin,'fits_same_bank_in_model':margin>=0,
            'layout':layout,
            'not_implemented':['token ID allocation','6502 dictionary table lookup',
              'preservation of native control bytes and entry semantics',
              'real dialogue line breaks/screen width','NES runtime verification']}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tokens',type=int,required=True)
    p.add_argument('--encoded-symbols',type=int,required=True)
    p.add_argument('--phrase-data-bytes',type=int,required=True)
    args=p.parse_args()
    print(json.dumps(plan(encoded_symbols=args.encoded_symbols,tokens=args.tokens,
                          dictionary_phrase_data_bytes=args.phrase_data_bytes),indent=2))
if __name__=='__main__':main()
