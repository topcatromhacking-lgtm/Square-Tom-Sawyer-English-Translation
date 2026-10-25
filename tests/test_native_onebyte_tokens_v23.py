"""v23 original 6502 one-byte native token conversion and whole-Bank6 repack."""
from __future__ import annotations
import sys,unittest,hashlib,zipfile,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_onebyte_tokens_v23 as mod
ROM=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

class SourceFree(unittest.TestCase):
    def test_single_reference_to_onebyte(self):
        raw=b'\x00\x00ABC\x03\x02D\x00'
        result,count=mod.converted_body(raw)
        self.assertEqual((result,count),(b'\x00\x00ABC\xD1D\x00',1))
    def test_source_non_token_bytes_preserved(self):
        b=b'\x00\x00\x01\x02\x0a\x8f\x00'
        self.assertEqual(mod.converted_body(b),(b,0))
    def test_reject_collision_with_existing_glyph(self):
        with self.assertRaisesRegex(ValueError,'collides'):
            mod.converted_body(b'\x00\x00\xd0\x00')
    def test_reject_outside_known_29_references(self):
        with self.assertRaisesRegex(ValueError,'not in shared phrase'):
            mod.converted_body(b'\x00\x00\x03\x1e\x00')
    def test_original_and_singlebyte_semantic_equivalence(self):
        targets=[b'\x00\x00ONE\x00',b'\x00\x00TWO\x00']
        old=b'\x00\x00\x03\x01-\x03\x02\x00'
        new,_=mod.converted_body(old)
        self.assertEqual(mod.expand_body(old,targets,new_mode=False),b'ONE-TWO')
        self.assertEqual(mod.expand_body(new,targets,new_mode=True),b'ONE-TWO')
    def test_all_29_token_pointer_indices(self):
        for index in range(1,30):
            token=mod.FIRST_TOKEN+index-1
            self.assertLessEqual(token,mod.LAST_TOKEN)
            self.assertEqual(token-0xCF,index)
            self.assertEqual(0x8002+2*(token-0xCF),0x8002+2*index)
    def test_resolver_patch_exact_in_place(self):
        self.assertEqual(len(mod.NEW_DISPATCH),len(mod.ORIG_DISPATCH))
        self.assertEqual(len(mod.NEW_RESOLVER),len(mod.ORIG_RESOLVER))
        self.assertEqual(mod.NEW_DISPATCH.hex(),'c9d09006')
        self.assertEqual(mod.NEW_RESOLVER.hex(),'38e9cf85f1a90085f2')

@unittest.skipUnless(ROM.exists(),'Commercial original ROM unavailable in CI')
class ExactRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROM) as z:cls.source=z.read('Square no Tom Sawyer (Japan).nes')
        cls.fw,cls.rollback,cls.report=mod.build(cls.source)
        cls.patched=mod.v16.apply_ips(cls.source,cls.fw)
        cls.recs,_=mod.get_record_map(cls.source)
    def test_all_479_expansions_equal(self):
        old=mod.original_raw(self.source,self.recs)
        shifted=[]
        for rec in self.recs:
            at=int(rec['table_file_offset'],16)
            ptr=struct.unpack_from('<H',self.patched,at)[0]
            ofs=mod.BANK6_START+ptr-0x8000
            stop=self.patched.find(b'\x00',ofs+2)
            self.assertGreater(stop,ofs+1)
            shifted.append(self.patched[ofs:stop+1])
        for i,(before,after) in enumerate(zip(old,shifted)):
            self.assertEqual(before[:2],after[:2])
            self.assertEqual(mod.expand_body(before,old[:29],new_mode=False),
                             mod.expand_body(after,shifted[:29],new_mode=True),f'record {i}')
    def test_saves_237_actual_bytes(self):
        self.assertEqual(self.report['references_reencoded'],237)
        self.assertEqual(self.report['reclaimed_bank6_bytes'],237)
        self.assertEqual(self.report['repacked_script_bytes'],14088)
        self.assertEqual(self.report['original_script_bytes'],14325)
    def test_exact_original_rollback(self):
        self.assertEqual(mod.v16.apply_ips(self.patched,self.rollback),self.source)
        self.assertEqual(hashlib.sha256(self.patched).hexdigest(),self.report['patched_sha256'])
    def test_header_delimiters_and_all_pointers(self):
        pointers=[]
        for r in self.recs:
            at=int(r['table_file_offset'],16)
            pointers.append(struct.unpack_from('<H',self.patched,at)[0])
        self.assertEqual(pointers,sorted(set(pointers)))
        self.assertEqual(self.report['moved_pointers'],445)
        for at in (0x18010,0x18012,0x1820a,0x18252,0x1834a,0x18382,0x18410):
            self.assertEqual(self.patched[at:at+2],self.source[at:at+2])
    def test_fixed_6502_patch_exact_and_no_else(self):
        base=mod.v16.apply_ips(self.source,mod.v17.build(self.source)[0])
        allowed=set(range(0x18812,0x1c007))
        allowed.update(k for r in self.recs for k in (int(r['table_file_offset'],16),int(r['table_file_offset'],16)+1))
        allowed.update(range(mod.at_cpu(mod.DISPATCH_CPU),mod.at_cpu(mod.DISPATCH_CPU)+4))
        allowed.update(range(mod.at_cpu(mod.RESOLVER_CPU),mod.at_cpu(mod.RESOLVER_CPU)+9))
        self.assertFalse({i for i,(a,b) in enumerate(zip(base,self.patched)) if a!=b}-allowed)
        self.assertEqual(self.patched[mod.at_cpu(mod.DISPATCH_CPU):mod.at_cpu(mod.DISPATCH_CPU)+4],mod.NEW_DISPATCH)
        self.assertEqual(self.patched[mod.at_cpu(mod.RESOLVER_CPU):mod.at_cpu(mod.RESOLVER_CPU)+9],mod.NEW_RESOLVER)
    def test_no_original_03_opcode_remains_in_indexed_text(self):
        for r in self.recs:
            at=int(r['table_file_offset'],16)
            ptr=struct.unpack_from('<H',self.patched,at)[0]
            start=mod.BANK6_START+ptr-0x8000
            end=self.patched.index(0,start+2)
            self.assertNotIn(3,self.patched[start+2:end])
    def test_original_source_gate(self):
        data=bytearray(self.source);data[0x1be6b]^=1
        with self.assertRaisesRegex(ValueError,'Exact source'):
            mod.build(bytes(data))

if __name__=='__main__':unittest.main()
