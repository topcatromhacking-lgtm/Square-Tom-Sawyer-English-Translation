"""Tests for private dump/edit/inject flow. Exact-ROM tests run if source is present."""
import csv,hashlib,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import script_pipeline_v18 as p

SRC=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

class PureTests(unittest.TestCase):
    def test_reference_parse(self):
        text='//POINTER #2 @ $21251 - STRING #2 @ $212EC\n#W16($21251)\nJP[ED]\nHello, Tom!\n'
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'demo.txt';f.write_text(text,encoding='utf8')
            ref=p.references(f)
        self.assertEqual(ref[0]['ptr'],0x21251)
        self.assertEqual(ref[0]['text'],0x212ec)
        self.assertEqual(ref[0]['english'],'Hello, Tom!')
    def test_discrepancy_markers(self):
        rows=[dict(ptr_at='0x1820A',text_at='0x2000F',english='',status='unreviewed',notes='')]
        extern=[dict(ptr=0x18252,text=0x2000f,english='',filename='x')]
        _,conf=p.merge(rows,extern)
        self.assertEqual(conf[0]['reason'],'GROUP_DELIMITER_FFFF')
    def test_exact_pointer_matching(self):
        rows=[dict(ptr_at='0x21251',text_at='0x212EC',english='',status='unreviewed',notes='')]
        refs=[dict(ptr=0x21251,text=0x212EC,english='HELLO',filename='external')]
        r,c=p.merge(rows,refs)
        self.assertEqual(c,[])
        self.assertEqual(r[0]['status'],'draft')
        self.assertEqual(r[0]['english'],'HELLO')
    def test_mismatch_quarantine(self):
        rows=[dict(ptr_at='0x21251',text_at='0x212EC',english='',status='unreviewed',notes='')]
        refs=[dict(ptr=0x21251,text=0x12345,english='BAD',filename='external')]
        r,c=p.merge(rows,refs)
        self.assertEqual(r[0]['english'],'')
        self.assertGreaterEqual(len(c),1)
    def test_diff_ips_roundtrip(self):
        a=b'hello world'
        b=b'hello WORLD'
        ips=p.diff_ips(a,b)
        self.assertEqual(p.v16.apply_ips(a,ips),b)

@unittest.skipUnless(SRC.exists(),'Exact Japanese game source not provided')
class OriginalRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=p.read_source(SRC)
        cls.rows=p.inventory(cls.original)
    def test_inventory_520_and_groups(self):
        self.assertEqual(len(self.rows),520)
        self.assertEqual(sum(r['bank']=='6' for r in self.rows),479)
        self.assertEqual(sum(r['bank']=='8' for r in self.rows),41)
        self.assertEqual([sum(r['group']==str(g) for r in self.rows) for g in range(1,5)],[251,35,123,70])
        self.assertEqual(sum(int(x['allocated']) for x in self.rows[:479]),14325)
    def test_records_source_matches_hash_and_terminator(self):
        for rec in self.rows:
            blob=bytes.fromhex(rec['raw_hex'])
            self.assertEqual(len(blob),int(rec['allocated']))
            self.assertEqual(blob[-1],0)
            self.assertEqual(hashlib.sha256(blob).hexdigest(),rec['original_sha256'])
    def test_approved_intro_reproduces_real_v17_rom(self):
        rows=[r.copy() for r in self.rows]
        for i,s in enumerate(p.v16.TEXTS):
            rows[479+i]['english']=s.replace('\n','\\n')
            rows[479+i]['status']='approved'
        ips,undo,result=p.inject(self.original,rows)
        prior=p.v17.build(self.original)[0]
        self.assertEqual(p.v16.apply_ips(self.original,ips),p.v16.apply_ips(self.original,prior))
        self.assertEqual(p.v16.apply_ips(p.v16.apply_ips(self.original,ips),undo),self.original)
        self.assertEqual(result['patched_sha256'],'5d869aa02c3c72cb06cefedd159e77f30d7cc18f630d7e1a4356ffaa94e7d34d')
    def test_tsv_mutation_guard(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'master.tsv'
            p.dump(self.original,path,[],True,None)
            with path.open(newline='',encoding='utf8') as f: rows=list(csv.DictReader(f,delimiter='\t'))
            rows[0]['ptr_at']='0x12345'
            with path.open('w',newline='',encoding='utf8') as f:
                w=csv.DictWriter(f,fieldnames=p.FIELDS,delimiter='\t');w.writeheader();w.writerows(rows)
            with self.assertRaisesRegex(ValueError,'Original field changed'):
                p.load_edited(self.original,path)
    def test_bank6_injection_guard(self):
        rows=[r.copy() for r in self.rows]
        rows[0]['status']='approved';rows[0]['english']='YES'
        with self.assertRaisesRegex(ValueError,'Bank 6'):
            p.inject(self.original,rows)
    def test_overflow_rejection(self):
        rows=[r.copy() for r in self.rows]
        for i,s in enumerate(p.v16.TEXTS):
            rows[479+i]['status']='approved'
            rows[479+i]['english']=s.replace('\n','\\n')
        rows[479]['english']='A'*20+'\\n'+'B'*20+'\\n'+'C'*20
        with self.assertRaisesRegex(ValueError,'overflows'):
            p.inject(self.original,rows)
    def test_real_second_window_one_record(self):
        rows=[r.copy() for r in self.rows]
        for i,s in enumerate(p.v16.TEXTS):
            rows[479+i]['status']='approved';rows[479+i]['english']=s.replace('\n','\\n')
        rows[479+12]['status']='approved';rows[479+12]['english']='HELLO'
        ips,back,report=p.inject(self.original,rows)
        new=p.v16.apply_ips(self.original,ips)
        self.assertEqual(p.v16.apply_ips(new,back),self.original)
        base=p.v16.apply_ips(self.original,p.v17.build(self.original)[0])
        self.assertEqual(new[:0x21265],base[:0x21265])
        self.assertEqual(new[0x2129F:p.v16.TEXT_END],base[0x2129F:p.v16.TEXT_END])
        self.assertEqual(new[p.BANK8_DATA_END:],base[p.BANK8_DATA_END:])
        self.assertNotEqual(hashlib.sha256(new).hexdigest(),p.v17.V16_SHA)

if __name__=='__main__':unittest.main()
