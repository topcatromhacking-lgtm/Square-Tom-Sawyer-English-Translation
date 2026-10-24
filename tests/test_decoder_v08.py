"""Source-free regression checks of original-ROM character decoder."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from analyze_decoder_v08 import convert,rom_offset,verify
class ConverterTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual((convert(0x70)["A"],convert(0x70)["Y"]),(0xE0,0xFF))
    def test_reserved_8e(self):
        self.assertEqual((convert(0x8e)["A"],convert(0x8e)["Y"]),(0xFE,0xFF))
    def test_space(self):
        self.assertEqual((convert(0x8f)["A"],convert(0x8f)["Y"]),(0xFF,0xFF))
    def test_v06_composite(self):
        self.assertEqual((convert(0x9b)["A"],convert(0x9b)["Y"]),(0xA8,0x7E))
        self.assertEqual((convert(0xa4)["A"],convert(0xa4)["Y"]),(0xB6,0x7E))
        self.assertEqual((convert(0xa5)["A"],convert(0xa5)["Y"]),(0xB7,0x7E))
    def test_ranges(self):
        self.assertEqual((convert(0x90)["A"],convert(0x90)["Y"]),(0x9D,0x7E))
        self.assertEqual((convert(0xb0)["A"],convert(0xb0)["Y"]),(0xD3,0x7E))
        self.assertEqual((convert(0xc4)["A"],convert(0xc4)["Y"]),(0xB1,0x7F))
        self.assertEqual((convert(0xc9)["A"],convert(0xc9)["Y"]),(0xE7,0x7F))
    def test_special(self): self.assertIsNone(convert(8)["Y"])
    def test_bank8(self): self.assertEqual(rom_offset(8,0x8391),0x203A1)
    def test_bank15(self): self.assertEqual(rom_offset(15,0xEE50),0x3EE60)
    def test_wrong_rom(self):
        with self.assertRaises(ValueError): verify(bytes(262160))
    def test_bad_code(self):
        with self.assertRaises(ValueError): convert(256)
if __name__=="__main__":unittest.main()
