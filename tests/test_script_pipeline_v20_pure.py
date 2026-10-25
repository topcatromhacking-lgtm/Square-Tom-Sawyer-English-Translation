"""ROM-independent v2.0 engine tests, always executed by public CI."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import script_pipeline_v20 as v

class PureTests(unittest.TestCase):
    def test_header_and_english_encoding(self):
        self.assertEqual(v.encode_preserving_header(b'\x00\x00\x45\x00','HI'),
                         b'\x00\x00\x75\x76\x00')
    def test_unknown_header_requires_explicit_gate(self):
        with self.assertRaisesRegex(ValueError,'complex header'):
            v.encode_preserving_header(b'\x1b\x04\x45\x00','HI')
        self.assertEqual(v.encode_preserving_header(b'\x1b\x04\x45\x00','HI',allow_complex_header=True)[:2],b'\x1b\x04')
    def test_no_bad_controls_or_source(self):
        with self.assertRaisesRegex(ValueError,'original record'):
            v.encode_preserving_header(b'\x00\x00\x00A\x00','HI')
        with self.assertRaisesRegex(ValueError,'Unsupported glyph'):
            v.encode_preserving_header(b'\x00\x00\x45\x00','HÉ')
    def test_repack_compensated_growth(self):
        left=v.encode_preserving_header(b'\x00\x00X\x00','HELLO')
        right=v.encode_preserving_header(b'\x00\x00LONGER\x00','HI')
        self.assertEqual(v.pack_original_window([left,right],12),None)
        self.assertEqual(v.pack_original_window([left,right],15),left+right+bytes(2))
    def test_repack_invalid_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'broken record'):
            v.pack_original_window([b'NON-TERMINATED'],20)

if __name__=='__main__':unittest.main()
