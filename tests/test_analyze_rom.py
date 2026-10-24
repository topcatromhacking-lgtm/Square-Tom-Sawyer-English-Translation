"""Source-free regression tests for the Square no Tom Sawyer ROM analyzer."""
import hashlib
import pathlib
import struct
import sys
import unittest
import zlib
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import analyze_rom


class AnalyzerTests(unittest.TestCase):
    def test_bad_ines(self):
        with self.assertRaisesRegex(ValueError, "iNES"):
            analyze_rom.identity(b"invalid")

    def test_reject_wrong_rom(self):
        sample = bytearray(262160)
        sample[:16] = bytes.fromhex("4e45531a100012000000000000000000")
        with self.assertRaisesRegex(ValueError, "Wrong base ROM"):
            analyze_rom.get_record_map(bytes(sample))

    def test_reject_other_input_extension(self):
        with self.assertRaisesRegex(ValueError, "Input must"):
            analyze_rom.read_source(pathlib.Path("example.bad"))

    def test_valid_synthetic_pointer_table(self):
        rom = bytearray(262160)
        rom[:16] = bytes.fromhex("4e45531a100012000000000000000000")
        rom[analyze_rom.ROM_BANK_START + 2:analyze_rom.TABLE_END] = (
            b"\xff" * (analyze_rom.TABLE_END - analyze_rom.ROM_BANK_START - 2))
        struct.pack_into("<H", rom, analyze_rom.ROM_BANK_START, 0xBFF7)
        struct.pack_into("<H", rom, analyze_rom.ROM_BANK_START + 4, 0x8802)
        data = bytes(rom)
        sha1 = hashlib.sha1(data).hexdigest()
        crc32 = f"{zlib.crc32(data) & 0xffffffff:08X}"
        with mock.patch.object(analyze_rom, "EXPECTED_SHA1", sha1), \
             mock.patch.object(analyze_rom, "EXPECTED_CRC32", crc32):
            records, summary = analyze_rom.get_record_map(data)
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["group_counts"], [1])
        self.assertEqual(summary["text_span_bytes"], 14325)
        self.assertEqual(records[0]["cpu_pointer"], "0x8802")
        self.assertEqual(records[0]["terminator"], "0x00")


if __name__ == "__main__":
    unittest.main()
