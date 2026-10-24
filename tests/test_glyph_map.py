"""Source-free partial glyph table tests."""
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from decode_indexed_text import load_map,decode_raw

class GlyphMappingTests(unittest.TestCase):
    def test_glyph_count(self):
        self.assertEqual(len(load_map()),88)
    def test_known_words(self):
        m=load_map()
        self.assertEqual(decode_raw(bytes.fromhex("C2 8D 64 0B"),m),"ベッキー")
        self.assertEqual(decode_raw(bytes.fromhex("5F 0B 6A 71 69 70 57"),m),"イーストシティ")
        self.assertEqual(decode_raw(bytes.fromhex("70 6A 71"),m),"テスト")
    def test_unknowns_remain_visible(self):
        self.assertEqual(decode_raw(bytes.fromhex("00 01 FF"),load_map()),"<00><01><FF>")

if __name__=="__main__":unittest.main()
