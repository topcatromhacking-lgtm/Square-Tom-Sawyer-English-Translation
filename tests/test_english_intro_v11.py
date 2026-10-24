"""Source-free v1.1 font and opening-line checks."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from make_english_intro_v11 import (HEX_GLYPHS,GLYPH_CODES,LINES,make,SOURCE,PATCHED)
from make_intro_probe import ips_apply
import hashlib

class EnglishIntroTests(unittest.TestCase):
 def test_37_character_font(self):
  self.assertEqual(len(GLYPH_CODES),37)
  self.assertEqual(set(GLYPH_CODES),set(HEX_GLYPHS))
  self.assertEqual(len(set(GLYPH_CODES.values())),37)
 def test_bitmap_shape(self):
  for c,bitmap in HEX_GLYPHS.items():
   self.assertEqual(len(bytes.fromhex(bitmap)),8,c)
   self.assertEqual(bytes.fromhex(bitmap)[0],0,c)
 def test_intro_line_lengths(self):
  self.assertEqual([len(english) for _,english,_ in LINES],[7,8,15])
  self.assertEqual([len(old) for _,_,old in LINES],[12,9,15])
  self.assertEqual([ofs for ofs,_,_ in LINES],[0x2129F,0x212AC,0x212B6])
 def test_source_checksum_guard(self):
  with self.assertRaises(ValueError):make(bytes(262160))
 def test_source_fixture_rejects_modified_intro(self):
  raw=bytearray(262160)
  for ofs,_,old in LINES:raw[ofs:ofs+len(old)]=old
  raw[0x212AB]=1;raw[0x212B5]=1
  with self.assertRaises(ValueError):make(bytes(raw))
 def test_letter_encoding(self):
  self.assertEqual(GLYPH_CODES["A"],0x20)
  self.assertEqual(GLYPH_CODES["Z"],0x39)
  self.assertEqual(GLYPH_CODES["0"],0x3A)
  self.assertEqual(GLYPH_CODES["9"],0x43)
  self.assertEqual(GLYPH_CODES[","],0x44)
 def test_all_bytes_are_printable_or_space(self):
  for _,line,_ in LINES:
   self.assertTrue(all(c==" " or c in GLYPH_CODES for c in line))
 def test_source_hash_is_pinned(self):
  self.assertEqual(len(SOURCE),64)
  self.assertEqual(len(PATCHED),64)
if __name__=="__main__":unittest.main()
