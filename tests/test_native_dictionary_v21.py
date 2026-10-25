"""v21 original 6502 native-reference audit and nonnested dictionary tests."""
import sys,unittest,zipfile,hashlib,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_dictionary_v21 import audit_native,estimate_flat,load_english,SHA
ROM=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')

class Model(unittest.TestCase):
    def test_flat_non_nested_roundtrip(self):
        d=estimate_flat(['HELLO HELLO','HELLO WORLD','WORLD!'],token_limit=12)
        self.assertTrue(d['lossless_abstract_roundtrip'])
        self.assertGreater(d['non_nested_phrase_tokens'],0)
        self.assertLess(d['estimates'][-1]['estimated_bank6_bytes'],d['estimates'][0]['estimated_bank6_bytes'])
    def test_enforces_budget(self):
        for n in (-1,191):
            with self.assertRaises(ValueError):estimate_flat(['HI'],token_limit=n)
    def test_rejects_unicode(self):
        with self.assertRaises(ValueError):estimate_flat(['HELLO — TOM'])
    def test_rejects_empty_and_bad_window(self):
        with self.assertRaises(ValueError):estimate_flat([])
        with self.assertRaises(ValueError):estimate_flat(['HELLO'],max_phrase_length=1)
    def test_record_boundaries_not_compressed_together(self):
        d=estimate_flat(['A','B','C'],token_limit=20)
        self.assertEqual(d['non_nested_phrase_tokens'],0)
    def test_newline_barrier(self):
        d=estimate_flat(['HELLO\\nWORLD','HELLO\\nWORLD'],token_limit=10)
        self.assertTrue(d['lossless_abstract_roundtrip'])
    def test_dictionary_storage_components(self):
        d=estimate_flat(['HELLO HELLO','HELLO HELLO'],token_limit=1)
        end=d['estimates'][-1]
        self.assertEqual(end['dictionary_index_bytes'],2)
        self.assertEqual(end['total_dictionary_storage'],end['dictionary_index_bytes']+end['dictionary_data_bytes'])
    def test_private_tsv_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fake.tsv'
            p.write_text('bank\tenglish\n6\tHI\n')
            with self.assertRaises(ValueError):load_english(p)

@unittest.skipUnless(ROM.exists(),'Original commercial Japanese ROM is unavailable in public CI')
class SourceRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROM) as z:cls.data=z.read('Square no Tom Sawyer (Japan).nes')
    def test_native_reference_usage(self):
        report=audit_native(self.data)
        self.assertEqual(report['native_reference_occurrences'],237)
        self.assertEqual(report['unique_reference_targets'],29)
        self.assertEqual(report['referencing_source_records'],172)
        self.assertEqual(report['target_indexes'],list(range(1,30)))
        self.assertEqual(report['nested_reference_targets'],[])
        self.assertEqual(report['absent_unmodified_body_byte_values'],90)
    def test_original_blank_region(self):
        r=audit_native(self.data)
        self.assertTrue(r['bank5_region_is_all_zero'])
        self.assertEqual(r['bank5_zero_region_bytes'],1160)
    def test_read_only_and_sha(self):
        before=hashlib.sha256(self.data).hexdigest()
        self.assertEqual(before,SHA)
        audit_native(self.data)
        self.assertEqual(hashlib.sha256(self.data).hexdigest(),before)
    def test_wrong_source_refused(self):
        edited=bytearray(self.data);edited[0x3EDF7]=0
        with self.assertRaises(ValueError):audit_native(bytes(edited))

if __name__=='__main__':unittest.main()
