"""v27 early accessible English pilot: source-gated checks on private original ROM."""
import hashlib,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import accessible_english_pilot_v27 as pilot
from analyze_rom import read_source,get_record_map
from english_codec_v15 import decode
ROM=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

@unittest.skipUnless(ROM.exists(),'Commercial ROM not available in source-only CI')
class OriginalRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=read_source(ROM)
        cls.fw,cls.back,cls.info=pilot.build(cls.original)
        cls.new=pilot.v23.v16.apply_ips(cls.original,cls.fw)
        oldfw,_,_=pilot.v23.build(cls.original)
        cls.base=pilot.v23.v16.apply_ips(cls.original,oldfw)
        cls.records,_=get_record_map(cls.original)
    def test_exact_source_to_patch_and_reverse(self):
        self.assertEqual(pilot.v23.v16.apply_ips(self.new,self.back),self.original)
        self.assertEqual(hashlib.sha256(self.new).hexdigest(),'cd64be1a795409474ce98642177af56e9869ef10a36b4cc5f1cdd732b3f1053a')
        self.assertEqual(self.info['forward_ips_sha256'],'a3bce22df8caf23a736817f9b20bda9d9676d4f8ec0b76c1f550ef9f1c958de1')
    def test_479_source_dialogue_pointers_not_changed(self):
        for r in self.records:
            p=int(r['table_file_offset'],16)
            self.assertEqual(self.new[p:p+2],self.base[p:p+2])
    def test_nearby_trace_b861_is_b6356(self):
        a,b,record=pilot.record_slice(self.new,self.records,356)
        self.assertEqual(a,0x1B86E)
        self.assertEqual(a+3,0x18010+0xB861-0x8000)
        self.assertEqual(record[:9],bytes.fromhex('0000ef0201ed01ee00'))
        self.assertEqual(record[9:],bytes(len(record)-9))
    def test_unmodified_other_478_records(self):
        for i,r in enumerate(self.records[:-1]):
            if i==356:continue
            _,_,current=pilot.record_slice(self.new,self.records,i)
            self.assertEqual(current,pilot.record_slice(self.base,self.records,i)[2])
    def test_29_shared_targets_unchanged(self):
        for i in range(1,30):
            p=int(self.records[i-1]['table_file_offset'],16)
            self.assertEqual(self.new[0x1BF34+i*2:0x1BF36+i*2],self.base[p:p+2])
    def test_three_exact_new_english_phrases(self):
        self.assertEqual(self.info['dictionary_token_count'],32)
        for x in self.info['new_phrase_tokens']:
            ofs=0x18010+int(x['cpu_pointer'],16)-0x8000
            original=self.new[ofs:ofs+x['encoded_bytes']]
            self.assertEqual(original[:2],b'\0\0')
            self.assertEqual(decode(original[2:]),x['english'])
    def test_previous_unreachable_hello_probe_not_retained(self):
        self.assertEqual(pilot.record_slice(self.new,self.records,420)[2],
                         pilot.record_slice(self.base,self.records,420)[2])
    def test_english_intro_and_commands_kept(self):
        for a,b in ((0x2124D,0x213EC),(0x3D1AF,0x3D1CB)):
            self.assertEqual(self.new[a:b],self.base[a:b])
    def test_88_bytes_tail_left(self):
        self.assertEqual(self.info['free_tail_bytes'],88)
        self.assertEqual(self.new[0x1BFAF:0x1C007],bytes(88))
    def test_source_lock(self):
        r=bytearray(self.original);r[0x10]^=1
        with self.assertRaises(ValueError):pilot.build(bytes(r))
if __name__=='__main__':unittest.main()
