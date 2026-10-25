"""v2.0 metadata-preserving whole-bank repointing, offline reference tests."""
import hashlib,sys,unittest,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import script_pipeline_v20 as v

ROM=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

@unittest.skipUnless(ROM.exists(),'The commercial source ROM is not present (source-only CI)')
class WholeBankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=v.read_source(ROM)
        cls.baseline=v.v18.v16.apply_ips(cls.source,v.v18.v17.build(cls.source)[0])
        cls.cleanrows=v.v18.inventory(cls.source)
        assert len(cls.cleanrows)==520
    def rows(self):return [r.copy() for r in self.cleanrows]
    def test_no_approved_bank6_is_byte_exact(self):
        product,plan=v.compile_bank6(self.source,self.source,self.rows())
        self.assertEqual(product,self.source)
        self.assertEqual((plan['records'],plan['moved_indexed_pointers']),(479,0))
        self.assertEqual(plan['original_capacity_bytes'],14325)
    def test_repoint_growth_offset_by_shrink(self):
        rows=self.rows()
        rows[0]['english']='HELLO';rows[0]['status']='approved'
        rows[1]['english']='HI';rows[1]['status']='approved'
        result,plan=v.compile_bank6(self.source,self.baseline,rows)
        self.assertIsNotNone(result)
        self.assertEqual(plan['approved_simple'],2)
        self.assertEqual(plan['net_growth_bytes'],-5)
        self.assertEqual(plan['available_padding_bytes'],5)
        self.assertEqual(plan['moved_indexed_pointers'],478)
        self.assertEqual(struct.unpack_from('<H',result,0x18014)[0],0x8802)
        self.assertEqual(struct.unpack_from('<H',result,0x18016)[0],0x880A)
        self.assertEqual(struct.unpack_from('<H',result,0x18018)[0],0x880F)
        self.assertEqual(result[0x18812:0x1881A],b'\x00\x00\x75\x72\x79\x79\x7c\x00')
        self.assertEqual(result[0x1881A:0x1881F],b'\x00\x00\x75\x76\x00')
        self.assertEqual(result[v.BANK6_END:],self.baseline[v.BANK6_END:])
        self.assertEqual(result[:0x18010],self.baseline[:0x18010])
        self.assertEqual(result[0x18412:0x18812],self.baseline[0x18412:0x18812])
    def test_source_record_metadata_and_ffff_markers_survive(self):
        rows=self.rows()
        rows[0]['english']='HELLO';rows[0]['status']='approved'
        rows[1]['english']='HI';rows[1]['status']='approved'
        data,_=v.compile_bank6(self.source,self.baseline,rows)
        ptrs=[]
        original_records,_=v.get_record_map(self.source)
        for r in original_records:
            at=int(r['table_file_offset'],16)
            new=struct.unpack_from('<H',data,at)[0]
            s=v.BANK6_TABLE+new-0x8000
            self.assertEqual(data[s:s+2],self.source[int(r['text_file_offset'],16):int(r['text_file_offset'],16)+2])
            ptrs.append(new)
        self.assertEqual(ptrs,sorted(set(ptrs)))
        for at in (0x18010,0x18012,0x1820A,0x18252,0x1834A,0x18382,0x18410):
            self.assertEqual(data[at:at+2],self.source[at:at+2])
    def test_total_bank_overflow_rejected(self):
        rows=self.rows();rows[0]['english']='THIS IS VERY LONG';rows[0]['status']='approved'
        product,plan=v.compile_bank6(self.source,self.source,rows)
        self.assertIsNone(product)
        self.assertGreater(plan['overflow_bytes'],0)
        with self.assertRaisesRegex(ValueError,'full-bank overflow'):v.inject(self.source,rows)
    def test_bad_source_checksum(self):
        with self.assertRaisesRegex(ValueError,'Wrong original'):
            v.compile_bank6(self.source[:-1]+b'\x00',self.source,self.rows())
    def test_bad_original_metadata_field(self):
        rows=self.rows();rows[3]['raw_hex']='abcd'
        with self.assertRaisesRegex(ValueError,'Altered original TSV metadata'):
            v.compile_bank6(self.source,self.source,rows)
    def test_complex_header_denied_by_default(self):
        rows=self.rows();idx=30
        self.assertNotEqual(bytes.fromhex(rows[idx]['raw_hex'])[:2],b'\x00\x00')
        rows[idx]['status']='approved';rows[idx]['english']='HI'
        with self.assertRaisesRegex(ValueError,'complex header requires'):
            v.compile_bank6(self.source,self.source,rows)
    def test_complex_header_explicit_experiment_retains_header(self):
        rows=self.rows();idx=30
        rows[idx]['status']='approved';rows[idx]['english']='HI'
        data,plan=v.compile_bank6(self.source,self.source,rows,allow_complex_header=True)
        self.assertEqual(plan['approved_complex'],1)
        self.assertEqual(data[int(rows[idx]['text_at'],16):int(rows[idx]['text_at'],16)+2],b'\x0b\x01')
    def test_no_stack_of_existing_bank6_changes(self):
        modified=bytearray(self.baseline);modified[0x18814]^=1
        with self.assertRaisesRegex(ValueError,'Baseline already edits'):
            v.compile_bank6(self.source,bytes(modified),self.rows())
    def test_end_pointer_and_table_padding_stable(self):
        rows=self.rows();rows[1]['english']='HI';rows[1]['status']='approved'
        product,plan=v.compile_bank6(self.source,self.baseline,rows)
        self.assertEqual(product[0x18010:0x18014],self.source[0x18010:0x18014])
        self.assertEqual(product[0x1834A:0x18384],self.source[0x1834A:0x18384])
        self.assertEqual(product[0x1C007:0x1C010],self.source[0x1C007:0x1C010])
    def test_cumulative_forward_reverse(self):
        rows=self.rows()
        for i,s in enumerate(v.v18.v16.TEXTS):
            rows[479+i]['english']=s.replace('\n','\\n');rows[479+i]['status']='approved'
        rows[0]['english']='HELLO';rows[0]['status']='approved'
        rows[1]['english']='HI';rows[1]['status']='approved'
        ips,undo,manifest=v.inject(self.source,rows)
        final=v.v18.v16.apply_ips(self.source,ips)
        self.assertEqual(v.v18.v16.apply_ips(final,undo),self.source)
        self.assertTrue(manifest['rollback_exact'])
        self.assertEqual(manifest['moved_indexed_pointers'],478)
        self.assertEqual(final[0x2129F:0x213EC],self.baseline[0x2129F:0x213EC])
    def test_no_changes_cumulative_identical_v17(self):
        ips,back,manifest=v.inject(self.source,self.rows())
        final=v.v18.v16.apply_ips(self.source,ips)
        self.assertEqual(final,self.baseline)
        self.assertEqual(v.v18.v16.apply_ips(final,back),self.source)

if __name__=='__main__':unittest.main()
