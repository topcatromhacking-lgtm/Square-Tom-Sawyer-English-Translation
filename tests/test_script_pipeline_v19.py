"""v1.9 Bank 6 safety regressions. Original-ROM tests skip in source-only CI."""
import hashlib,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import script_pipeline_v19 as v

ROM=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

class PureSafety(unittest.TestCase):
    def setUp(self):
        original=bytearray(262160)
        original[0x18812:0x1881a]=b'\x00\x00\x34\x35\x36\x37\x38\x00'
        original[0x1881a:0x18825]=b'\x2b\x00\x34\x35\x36\x37\x38\x39\x3a\x3b\x00'
        self.source=bytes(original)
        self.sha=hashlib.sha256(self.source).hexdigest()
        self.rows=[{'status':'draft'} for _ in range(520)]
        self.rows[0]={'id':'B6-000','bank':'6','status':'approved','index':'0',
            'text_at':'0x18812','allocated':'8','raw_hex':self.source[0x18812:0x1881a].hex(),
            'english':'HI','group':'1'}
        self.rows[1]={'id':'B6-001','bank':'6','status':'draft','index':'1',
            'text_at':'0x1881A','allocated':'11','raw_hex':self.source[0x1881a:0x18825].hex(),
            'english':'HI','group':'1'}
    def runpatch(self,rows=None,baseline=None):
        with patch.object(v.v18,'SHA',self.sha):
            return v.patch_simple_bank6(self.source,baseline or self.source,rows or self.rows)
    def test_approved_edits_body_only_and_keeps_next_record(self):
        after,report=self.runpatch()
        self.assertEqual(after[0x18812:0x1881a],b'\x00\x00\x75\x76\x00\x00\x00\x00')
        self.assertEqual(after[0x1881a:],self.source[0x1881a:])
        self.assertEqual(report['approved_simple_records'],1)
        self.assertTrue(report['bank6_pointer_table_unchanged'])
    def test_refuse_complex_header(self):
        rows=[x.copy() for x in self.rows]
        rows[0]['status']='draft';rows[1]['status']='approved'
        with self.assertRaisesRegex(ValueError,'complex two-byte metadata'):self.runpatch(rows)
    def test_refuse_overflow(self):
        rows=[x.copy() for x in self.rows];rows[0]['english']='TOOLONG'
        with self.assertRaisesRegex(ValueError,'overflow'):self.runpatch(rows)
    def test_refuse_unsupported_characters(self):
        rows=[x.copy() for x in self.rows];rows[0]['english']='HÉ'
        with self.assertRaisesRegex(ValueError,'Unsupported glyph'):self.runpatch(rows)
    def test_refuse_bad_source_record(self):
        rows=[x.copy() for x in self.rows];rows[0]['raw_hex']='0000414141414100'
        with self.assertRaisesRegex(ValueError,'identity mismatch'):self.runpatch(rows)
    def test_refuse_already_modified_record(self):
        baseline=bytearray(self.source);baseline[0x18814]=0x99
        with self.assertRaisesRegex(AssertionError,'baseline overlaps'):
            self.runpatch(baseline=bytes(baseline))
    def test_refuse_wrong_source_checksum(self):
        with self.assertRaisesRegex(ValueError,'checksum'):
            v.patch_simple_bank6(self.source[:-1]+b'\x01',self.source,self.rows)
    def test_refuse_empty_approved_translation(self):
        rows=[x.copy() for x in self.rows];rows[0]['english']=''
        with self.assertRaisesRegex(ValueError,'approved without'):self.runpatch(rows)

@unittest.skipUnless(ROM.exists(),'Exact Japanese ROM unavailable in source-only CI')
class ExactRomIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=v.read_source(ROM)
        cls.rows=v.v18.inventory(cls.original)
    def test_group_header_distribution(self):
        data=v.classify(self.original,self.rows)
        self.assertEqual((data['simple_header'],data['complex_header']),(187,292))
        self.assertEqual([data['groups'][str(i)]['simple_header'] for i in range(1,5)],[36,7,74,70])
    def test_no_bank6_approvals_reproduces_v17(self):
        fw,bk,report=v.inject(self.original,self.rows)
        final=v.v18.v16.apply_ips(self.original,fw)
        baseline=v.v18.v16.apply_ips(self.original,v.v18.v17.build(self.original)[0])
        self.assertEqual(final,baseline)
        self.assertEqual(v.v18.v16.apply_ips(final,bk),self.original)
    def test_seeded_approved_record_exact_rollback(self):
        rows=[r.copy() for r in self.rows]
        for i,s in enumerate(v.v18.v16.TEXTS):
            rows[479+i]['english']=s.replace('\n','\\n');rows[479+i]['status']='approved'
        rows[0]['english']='HI';rows[0]['status']='approved'
        fw,bk,report=v.inject(self.original,rows)
        final=v.v18.v16.apply_ips(self.original,fw)
        baseline=v.v18.v16.apply_ips(self.original,v.v18.v17.build(self.original)[0])
        self.assertEqual(final[:0x18812],baseline[:0x18812])
        self.assertEqual(final[0x18812:0x18819],b'\x00\x00\x75\x76\x00\x00\x00')
        self.assertEqual(final[0x18819:],baseline[0x18819:])
        self.assertEqual(v.v18.v16.apply_ips(final,bk),self.original)
        self.assertEqual(report['approved_simple_records'],1)

if __name__=='__main__':unittest.main()
