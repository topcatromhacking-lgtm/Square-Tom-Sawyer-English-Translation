import hashlib,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_overworld_menu_v17 as v

class MenuTests(unittest.TestCase):
    def test_offsets(self):
        self.assertEqual([a for a,_,_ in v.MENU_FIELDS],[0x3d1af,0x3d1b6,0x3d1bf,0x3d1c8])
    def test_exact_direct_tiles(self):
        self.assertEqual([v.tiles(w,len(b)).hex() for _,b,w in v.MENU_FIELDS],
                         ['e9ecece8ff','f1dee8e2','e1e6e4','e6f1e2ea'])
    def test_bounded_fields(self):
        self.assertEqual(v.tiles('GO',5),bytes.fromhex('e4ecffffff'))
        with self.assertRaises(ValueError):v.tiles('EXAMINE',5)
    def test_reject_bad_english(self):
        for wrong in ['look','A B','ITEM?','']:
            with self.subTest(wrong=wrong):
                with self.assertRaises(ValueError):v.tiles(wrong,8)
    def test_duplicate_ips_rejected(self):
        p=v.v16.make_ips([(0x10,b'AA'),(0x11,b'BB')])
        with self.assertRaises(ValueError):v.ips_records(p)
    def test_bad_ips_trailer(self):
        with self.assertRaises(ValueError):v.ips_records(b'PATCH\x00\x00\x00\x00\x01aEOFextra')
    def test_separate_from_v16_source_windows(self):
        for at,expected,_ in v.MENU_FIELDS:
            self.assertTrue(at>=v.v16.TEXT_END)
            self.assertTrue(at+len(expected)<len(bytes(262160)))
    @unittest.skipUnless(Path('/mnt/data/Square no Tom Sawyer (Japan).zip').exists(),
                         'Original game not present in source-only CI')
    def test_exact_original_rom_build_and_rollback(self):
        with zipfile.ZipFile('/mnt/data/Square no Tom Sawyer (Japan).zip') as z:
            source=z.read('Square no Tom Sawyer (Japan).nes')
        forward,reverse,m=v.build(source)
        after=v.v16.apply_ips(source,forward)
        self.assertEqual(len(forward),868)
        self.assertEqual(m['menu_bytes_changed'],16)
        self.assertEqual(hashlib.sha256(after).hexdigest(),m['patched_sha256'])
        self.assertEqual(v.v16.apply_ips(after,reverse),source)
        baseline=v.v16.apply_ips(source,v.v16.build(source)[0])
        other={i for i,(a,b) in enumerate(zip(baseline,after)) if a!=b}
        allowed={at+i for at,b,_ in v.MENU_FIELDS for i in range(len(b))}
        self.assertEqual(other,allowed)

if __name__=='__main__':unittest.main()
