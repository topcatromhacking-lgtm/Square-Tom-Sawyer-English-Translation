"""Offline v22 native-reference smoke patch and no-nesting safety gates."""
from __future__ import annotations
import hashlib,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_reference_probe_v22 as mod
SOURCE=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')
class Pure(unittest.TestCase):
    def test_raw_single_reference_round_trip(self):
        target=b'\0\0ABCD\0'
        raw=b'\0\0ABCD\0'
        alias=b'\0\0\x03\x01\0\0'
        self.assertEqual(mod.expand_native(raw,[target]),b'ABCD')
        self.assertEqual(mod.expand_native(alias,[target]),b'ABCD')
    def test_reject_nested_reference(self):
        with self.assertRaisesRegex(ValueError,'Recursive'):
            mod.expand_native(b'\0\0\x03\x01\0',[b'\0\0\x03\x01\0'])
    def test_reject_unknown_reference(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):
            mod.expand_native(b'\0\0\x03\x02\0',[b'\0\0AB\0'])
    def test_reject_truncated_reference(self):
        with self.assertRaisesRegex(ValueError,'Truncated'):
            mod.expand_native(b'\0\0\x03\0',[b'\0\0AB\0'])
    def test_interior_terminator_rejected(self):
        with self.assertRaisesRegex(ValueError,'termination'):
            mod.expand_native(b'\0\0A\0B\0',[b'\0\0AB\0'])
@unittest.skipUnless(SOURCE.exists(),'Commercial Japanese source not installed in source-free CI')
class OriginalSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(SOURCE) as z:cls.source=z.read('Square no Tom Sawyer (Japan).nes')
    def test_source_verified_patch(self):
        fw,back,report=mod.build(self.source)
        patched=mod.v16.apply_ips(self.source,fw)
        self.assertEqual(mod.v16.apply_ips(patched,back),self.source)
        self.assertEqual(hashlib.sha256(patched).hexdigest(),report['patched_sha256'])
        self.assertEqual(report['reference_control'],'03 01')
        self.assertTrue(report['logical_stream_equal_original'])
        self.assertEqual(report['original_indexed_pointers_changed'],0)
    def test_exact_source_fingerprint_gate(self):
        data=bytearray(self.source);data[10]^=1
        with self.assertRaisesRegex(ValueError,'Exact unmodified'):
            mod.build(bytes(data))
    def test_all_candidate_targets_are_nonrecursive(self):
        allc=mod.eligible_duplicate_literals(self.source)
        self.assertIn((420,1),{(x['record'],x['reference_index']) for x in allc})
        self.assertNotIn(3,[x['record'] for x in allc])
        self.assertNotIn(16,[x['record'] for x in allc])
    def test_probe_does_not_change_native_reference_targets(self):
        fw,_,_=mod.build(self.source)
        patched=mod.v16.apply_ips(self.source,fw)
        for r in mod.get_record_map(self.source)[0][:29]:
            a=int(r['text_file_offset'],16)
            self.assertEqual(patched[a:a+r['length_bytes']],self.source[a:a+r['length_bytes']])
    def test_no_overlap_original_v17_patch(self):
        fw,_,_=mod.build(self.source)
        after=mod.v16.apply_ips(self.source,fw)
        original_fw,_,_=mod.v17.build(self.source)
        original_v17=mod.v16.apply_ips(self.source,original_fw)
        differences=[i for i,(a,b) in enumerate(zip(original_v17,after)) if a!=b]
        self.assertTrue(differences)
        self.assertTrue(set(differences).issubset(set(range(0x1BE6A,0x1BE71))))
if __name__=='__main__':unittest.main()
