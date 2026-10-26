"""v26 isolated Bank6 lookup regression against exact original source ROM.

The micro-runner executes the 25 instructions of the injected Bank6 helper to
establish the arithmetic of the table pointer. It is not an NES emulator.
"""
import hashlib,sys,struct,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import independent_dictionary_v26 as p
import native_onebyte_tokens_v23 as v23

SOURCE=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

def execute_helper(code:bytes,index:int)->tuple[int,int]:
    """Instruction-level 6502 subset for this exact original helper clone."""
    ram=bytearray(0x10000)
    a=0;y=index&255;carry=0;pc=0
    while pc<len(code):
        opcode=code[pc];pc+=1
        if opcode==0xea:continue
        if opcode==0x60:break
        if opcode in (0x8c,0x8d,0x0e,0x2e,0xad):
            addr=code[pc]|code[pc+1]<<8;pc+=2
            if opcode==0x8c:ram[addr]=y
            elif opcode==0x8d:ram[addr]=a
            elif opcode==0x0e:
                carry=(ram[addr]>>7)&1;ram[addr]=(ram[addr]<<1)&255
            elif opcode==0x2e:
                old=(ram[addr]>>7)&1
                ram[addr]=((ram[addr]<<1)|carry)&255
                carry=old
            else:a=ram[addr]
        elif opcode==0x18:carry=0
        elif opcode==0x69:
            value=code[pc];pc+=1;s=a+value+carry;a=s&255;carry=(s>>8)&1
        elif opcode==0xa8:y=a
        else:raise AssertionError(f'Unknown instruction {opcode:02X}')
    else:raise AssertionError('Subroutine did not return')
    return y,a

class PureTests(unittest.TestCase):
    def test_expected_source_helper(self):
        self.assertEqual(len(p.HELPER_TEMPLATE),25)
        self.assertEqual(p.HELPER_TEMPLATE[17],2)
        self.assertEqual(p.HELPER_TEMPLATE[23],0x80)
    def test_cpu_mapping(self):
        self.assertEqual(p.cpu_of(0x1BF1A),0xBF0A)
        self.assertEqual(p.cpu_of(0x1BF34),0xBF24)
    def test_helper_exec_original_base(self):
        for idx in (1,2,13,29,30):
            lo,hi=execute_helper(p.HELPER_TEMPLATE,idx)
            self.assertEqual(lo|hi<<8,0x8002+2*idx)
    def test_helper_exec_new_base(self):
        clone=bytearray(p.HELPER_TEMPLATE);clone[17]=0x24;clone[23]=0xBF
        for idx in range(1,31):
            lo,hi=execute_helper(clone,idx)
            self.assertEqual(lo|hi<<8,0xBF24+2*idx)
    def test_english_phrase_codec(self):
        from english_codec_v15 import encode
        self.assertEqual(encode('HELLO').data,bytes.fromhex('75 72 79 79 7C 00'))

@unittest.skipUnless(SOURCE.exists(),'Original Japanese ROM absent from public source-only CI')
class OriginalRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(SOURCE) as z:
            cls.original=z.read('Square no Tom Sawyer (Japan).nes')
        cls.fw,cls.undo,cls.result=p.compile(cls.original)
        cls.changed=p.v23.v16.apply_ips(cls.original,cls.fw)
        oldfw,_,_=v23.build(cls.original)
        cls.previous=v23.v16.apply_ips(cls.original,oldfw)
        cls.recs,_=p.get_record_map(cls.original)
    def test_30th_token_points_to_hello(self):
        table=0x1BF34;ptr=struct.unpack_from('<H',self.changed,table+60)[0]
        self.assertEqual(ptr,0xBF62)
        at=p.v23.BANK6_START+ptr-0x8000
        self.assertEqual(self.changed[at:at+8],bytes.fromhex('00 00 75 72 79 79 7C 00'))
    def test_previous_29_share_target_bytes(self):
        for i in range(1,30):
            tab=0x1BF34+2*i
            source_at=int(self.recs[i-1]['table_file_offset'],16)
            self.assertEqual(self.changed[tab:tab+2],self.previous[source_at:source_at+2])
    def test_479_primary_pointers_exactly_unchanged(self):
        for rec in self.recs:
            at=int(rec['table_file_offset'],16)
            self.assertEqual(self.changed[at:at+2],self.previous[at:at+2])
    def test_other_record_bodies_unchanged(self):
        for i,rec in enumerate(self.recs):
            if i==420:continue
            at=int(rec['table_file_offset'],16)
            cpu=struct.unpack_from('<H',self.changed,at)[0]
            offset=p.v23.BANK6_START+cpu-0x8000
            source_cpu=struct.unpack_from('<H',self.previous,at)[0]
            self.assertEqual(cpu,source_cpu)
            if i<len(self.recs)-1:
                end=p.v23.BANK6_START+struct.unpack_from('<H',self.previous,int(self.recs[i+1]['table_file_offset'],16))[0]-0x8000
            else:end=0x1BF1A
            self.assertEqual(self.changed[offset:end],self.previous[offset:end])
    def test_new_pilot_record_is_padded(self):
        rec=self.recs[420];cpu=struct.unpack_from('<H',self.changed,int(rec['table_file_offset'],16))[0]
        loc=p.v23.BANK6_START+cpu-0x8000
        self.assertEqual(self.changed[loc:loc+7],b'\0\0\xed\0\0\0\0')
    def test_helper_bytes_and_jsr_at_real_cpu_addresses(self):
        pos=p.v23.at_cpu(0xEE0A)
        self.assertEqual(self.changed[pos:pos+3],bytes.fromhex('20 0A BF'))
        helper=self.changed[0x1BF1A:0x1BF34]
        self.assertEqual(len(helper),26)
        self.assertEqual(helper[-1],0xEA)
        for i in range(1,31):
            lo,hi=execute_helper(helper,i)
            self.assertEqual((hi<<8)|lo,0xBF24+2*i)
    def test_new_diagnostic_leaves_header_intro_menu_untouched(self):
        self.assertEqual(self.changed[:16],self.previous[:16])
        self.assertEqual(self.changed[0x2124D:0x213EC],self.previous[0x2124D:0x213EC])
        self.assertEqual(self.changed[0x3D1AF:0x3D1CB],self.previous[0x3D1AF:0x3D1CB])
    def test_tail_bounds_and_unused_padding(self):
        self.assertEqual(self.result['tail_space_used'],96)
        self.assertEqual(self.result['unused_tail_bytes'],141)
        self.assertEqual(self.changed[0x1BF7A:0x1C007],bytes(141))
    def test_cumulative_ips_and_exact_rollback(self):
        self.assertEqual(p.v23.v16.apply_ips(self.changed,self.undo),self.original)
        self.assertEqual(hashlib.sha256(self.changed).hexdigest(),self.result['patched_sha256'])
    def test_wrong_source_refused(self):
        data=bytearray(self.original);data[33]^=1
        with self.assertRaisesRegex(ValueError,'Exact unmodified'):p.compile(bytes(data))

if __name__=='__main__':unittest.main()
