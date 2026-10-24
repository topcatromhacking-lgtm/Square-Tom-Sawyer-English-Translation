"""ROM-free tests of NES planar tile decoding and structural statistics."""
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from probe_encoding import tile_pixels, text_patterns, atlas, png_rgb


class FontProbeTests(unittest.TestCase):
    def setUp(self):
        self.rom = bytearray(16 + 16 * 0x4000)
        pos = 16 + 8 * 0x4000 + 224 * 16
        self.rom[pos] = 0x80
        self.rom[pos + 8] = 0x40

    def test_nes_2bitplanes(self):
        pixels = tile_pixels(bytes(self.rom), 8, 224)
        self.assertEqual(pixels[0], 1)
        self.assertEqual(pixels[1], 2)
        self.assertEqual(pixels[2:], [0] * 62)

    def test_reject_bad_indices(self):
        with self.assertRaises(ValueError):
            tile_pixels(bytes(self.rom), 16, 0)
        with self.assertRaises(ValueError):
            tile_pixels(bytes(self.rom), 8, 1024)

    def test_png_dimensions_and_offsets(self):
        image, info = atlas(bytes(self.rom), count=2, columns=1, scale=1)
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", image[16:24]), (8, 16))
        self.assertEqual(info["tiles"][0]["rom_file_offset"], "0x20E10")
        self.assertEqual(len(info["tiles"]), 2)

    def test_bad_image_rejected(self):
        with self.assertRaises(ValueError):
            png_rgb(10, 10, b"hello")

    def test_stat_patterns(self):
        data = b"\x00\x00\x22\x2b\x20\x00\x03\x22\x8f\x00"
        records = [{"text_file_offset": "0x00000", "length_bytes": 6},
                   {"text_file_offset": "0x00006", "length_bytes": 4}]
        stats = text_patterns(data, records)
        self.assertEqual(stats["record_count"], 2)
        self.assertEqual(stats["count_of_22_at_position_2"], 1)
        self.assertTrue(stats["terminator_00_at_end_of_all_records"])
        self.assertEqual(stats["total_bytes"], 10)


if __name__ == "__main__":
    unittest.main()
