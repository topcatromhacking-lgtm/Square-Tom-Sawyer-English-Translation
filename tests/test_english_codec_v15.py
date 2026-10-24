import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from english_codec_v15 import encode,decode

class EnglishCodecTests(unittest.TestCase):
    def test_history_letter_map(self):
        self.assertEqual(encode('AZ',terminate=False).data,b'\x6e\x87')
    def test_original_numeric_codes(self):
        self.assertEqual(encode('1855',terminate=False).data,b'\x11\x18\x15\x15')
    def test_intro_roundtrip(self):
        s='UNITED STATES\nMISSOURI\nYEAR 1855...'
        self.assertEqual(decode(encode(s).data),s)
    def test_punctuation(self):
        self.assertEqual(decode(encode("HI, TOM! I'M HERE.").data),"HI, TOM! I'M HERE.")
    def test_controls(self):
        self.assertEqual(encode('A\nB').data,b'\x6e\x01\x6f\x00')
    def test_deny_unsupported(self):
        with self.assertRaises(ValueError):encode('TOM—HUCK')
    def test_deny_implicit_wrap(self):
        with self.assertRaises(ValueError):encode('123456',maximum_chars_per_line=5)
    def test_deny_unterminated_decode(self):
        with self.assertRaises(ValueError):decode(b'\x6e\x00\x6f')
    def test_empty_line_deny(self):
        with self.assertRaises(ValueError):encode('A\n\nB')
