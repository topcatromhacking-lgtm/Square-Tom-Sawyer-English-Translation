#!/usr/bin/env python3
"""Source-free v28 tests. ROM-pinned end-to-end tests require the user's own ROM."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bulk_script_audit_v28 as v28


class V28AuditTests(unittest.TestCase):
    def test_wrap_and_explicit_break(self):
        lines, warnings = v28.wrapped_lines("THE ANGEL WHISPERED.[LN]THERE'S NOTHING[LN]FOR YOU HERE.")
        self.assertEqual(lines, ["THE ANGEL WHISPERED.", "THERE'S NOTHING", "FOR YOU HERE."])
        self.assertEqual(warnings, [])

    def test_wrap_long_unbreakable_word_is_not_silently_split(self):
        lines, warnings = v28.wrapped_lines("SUPERCALIFRAGILISTICEXPIALIDOCIOUS", 20)
        self.assertEqual(len(lines), 1)
        self.assertTrue(warnings)

    def test_controls_do_not_count_native_index_as_newline(self):
        result = v28.control_audit(bytes.fromhex("00 00 03 01 01 02 0A 00"))
        self.assertEqual(result["native_ref_count"], 1)
        self.assertEqual(result["byte_01_count"], 1)
        self.assertEqual(result["byte_02_count"], 1)
        self.assertEqual(result["low_bytes_unclassified"], "0A:1")

    def test_bad_native_operand_rejected(self):
        with self.assertRaises(ValueError):
            v28.control_audit(bytes.fromhex("00 00 03 20 00"))

    def test_bad_termination_rejected(self):
        with self.assertRaises(ValueError):
            v28.control_audit(bytes.fromhex("00 00 01 00 01"))

    def test_layout_preserves_record_id_and_splits_at_boundary(self):
        plan = v28.allocate_virtual_banks([
            {"id": "B6-000", "bytes": 8},
            {"id": "B6-001", "bytes": 5},
            {"id": "B6-002", "bytes": 0},
        ], capacity=10)
        self.assertEqual(plan["slot_occupancy"], [8, 5])
        self.assertEqual(plan["placements"][1]["slot"], 1)
        self.assertEqual(plan["placements"][2]["slot"], None)
        self.assertFalse(plan["bank_selection_hook_implemented"])

    def test_duplicates_and_too_large_fail(self):
        with self.assertRaises(ValueError):
            v28.allocate_virtual_banks([{"id": "a", "bytes": 2},
                                        {"id": "a", "bytes": 2}], 10)
        with self.assertRaises(ValueError):
            v28.allocate_virtual_banks([{"id": "b", "bytes": 11}], 10)

    def test_479_synthetic_source_inventory(self):
        source = bytes.fromhex("00 00 03 01 01 02 00")
        rows = [{
            "id": f"B6-{i:03d}", "bank": "6",
            "ptr_at": f"0x{0x18014 + 2*i:05X}",
            "text_at": f"0x{0x18812 + 7*i:05X}",
            "status": "draft", "raw_hex": source.hex(),
            "english": "THIS IS A SYNTHETIC FOUR LINE TEST FOR PAGING" if i == 7
                       else "HELLO", "notes": "",
        } for i in range(479)]
        review, stats, lengths = v28.review(rows)
        self.assertEqual(len(review), 479)
        self.assertEqual(stats["source_records"], 479)
        self.assertEqual(stats["source_native_references"], 479)
        self.assertEqual(stats["source_direct_01"], 479)
        self.assertEqual(stats["source_direct_02"], 479)
        self.assertEqual(review[0]["possible_overflow"], "NO")
        self.assertTrue(all(x["id"].startswith("B6-") for x in lengths))

    def test_unknown_markup_is_flagged_not_discarded(self):
        raw = "000048454c4c4f00"
        rows = [{
            "id": f"B6-{i:03d}", "bank": "6", "ptr_at": "0x18014",
            "text_at": "0x18812", "status": "draft", "raw_hex": raw,
            "english": "HELLO [WAIT]" if i == 5 else "HELLO", "notes": "",
        } for i in range(479)]
        table, stats, _ = v28.review(rows)
        self.assertEqual(stats["drafts_with_unresolved_markup"], 1)
        self.assertIn("[WAIT]", table[5]["unresolved_markup"])
        self.assertIn("[WAIT]", table[5]["english"])


if __name__ == "__main__":
    unittest.main()
