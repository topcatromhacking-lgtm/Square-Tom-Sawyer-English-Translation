"""Source-free tests; monkeypatched analyzer means no commercial ROM is needed."""
import hashlib
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import roundtrip_text


class RoundtripTests(unittest.TestCase):
    def setUp(self):
        self.data = b"AB\x00\x00C\x01\x00XYZZ"
        self.metas = [
            {"global_index": 0, "group": 1, "table_file_offset": "0x00000", "text_file_offset": "0x00000", "length_bytes": 3},
            {"global_index": 1, "group": 2, "table_file_offset": "0x00002", "text_file_offset": "0x00003", "length_bytes": 4},
        ]
        self.mock_map = mock.patch.object(roundtrip_text, "get_record_map",
                                          return_value=(self.metas, {"group_counts": [1, 1]}))
        self.mock_map.start()
        self.addCleanup(self.mock_map.stop)

    def test_exact_repack(self):
        extracted = roundtrip_text.extract(self.data)
        self.assertEqual(roundtrip_text.reconstruct(self.data, extracted), self.data)
        stats = roundtrip_text.statistics(extracted)
        self.assertEqual(stats["indexed_records"], 2)
        self.assertEqual(stats["total_bytes"], 7)

    def test_detect_modified_character(self):
        extracted = roundtrip_text.extract(self.data)
        extracted["entries"][1]["raw_hex"] = "00430101"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            roundtrip_text.reconstruct(self.data, extracted)

    def test_detect_modified_character_even_with_changed_hash(self):
        extracted = roundtrip_text.extract(self.data)
        edited = bytes.fromhex("00440100")
        extracted["entries"][1]["raw_hex"] = edited.hex()
        extracted["entries"][1]["sha256"] = hashlib.sha256(edited).hexdigest()
        with self.assertRaisesRegex(ValueError, "contents no longer match"):
            roundtrip_text.reconstruct(self.data, extracted)

    def test_reject_missing_record(self):
        extracted = roundtrip_text.extract(self.data)
        extracted["entries"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete record inventory"):
            roundtrip_text.reconstruct(self.data, extracted)

    def test_reject_moved_record(self):
        extracted = roundtrip_text.extract(self.data)
        extracted["entries"][0]["text_file_offset"] = "0x00009"
        with self.assertRaisesRegex(ValueError, "pointer or file offset"):
            roundtrip_text.reconstruct(self.data, extracted)

    def test_reject_other_rom(self):
        extracted = roundtrip_text.extract(self.data)
        with self.assertRaisesRegex(ValueError, "Base ROM fingerprint mismatch"):
            roundtrip_text.reconstruct(self.data + b"Z", extracted)

    def test_reject_invalid_schema(self):
        extracted = roundtrip_text.extract(self.data)
        extracted["schema"] = "other"
        with self.assertRaisesRegex(ValueError, "Wrong extraction schema"):
            roundtrip_text.reconstruct(self.data, extracted)


if __name__ == "__main__":
    unittest.main()
