#!/usr/bin/env python3
"""Static source-only invariants for the v29 read-only FCEUX witness."""
from pathlib import Path
import unittest


TRACER = Path(__file__).resolve().parents[1] / "tools" / "fceux_v29_pagination_witness.lua"


class PaginationWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TRACER.read_text(encoding="utf-8").lower()

    def test_all_operations_are_read_only(self):
        for forbidden in (
            "memory.write", "rom.write", "savestate.", "joypad.set",
            "memory.registerwrite", "emu.set", "file:write('patch",
        ):
            self.assertNotIn(forbidden, self.text)

    def test_runtime_dispatcher_and_secondary_reader_observed(self):
        self.assertIn("memory.registerexec(0xede7", self.text)
        self.assertIn("memory.registerexec(0xee2c", self.text)
        self.assertIn("memory.getregister('a')", self.text)

    def test_handles_low_control_bytes_without_assigning_page_semantics(self):
        self.assertIn("control_counts[token]", self.text)
        self.assertIn("unclassified", self.text)
        self.assertIn("0x7980", self.text)
        self.assertIn("0xf5", self.text)

    def test_bounded_trace_and_periodic_output(self):
        self.assertIn("max_events = 320", self.text)
        self.assertIn("emu.registerexit(report)", self.text)
        self.assertIn("frame-last_report>=120", self.text)


if __name__ == "__main__":
    unittest.main()
