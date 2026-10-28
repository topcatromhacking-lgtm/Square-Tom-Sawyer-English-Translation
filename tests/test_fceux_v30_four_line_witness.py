#!/usr/bin/env python3
"""Source-only checks for the v30 read-only witness."""
from pathlib import Path
import unittest


LUA = Path(__file__).resolve().parents[1] / "tools" / "fceux_v30_four_line_witness.lua"


class FourLineWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = LUA.read_text(encoding="utf-8").lower()

    def test_no_state_mutation(self):
        for forbidden in ("memory.write", "rom.write", "savestate.",
                          "joypad.set", "memory.registerwrite", "emu.set"):
            self.assertNotIn(forbidden, self.text)

    def test_pilot_fingerprint_and_f0_evidence(self):
        self.assertIn("0xf0,0x00", self.text)
        self.assertIn("token==0xf0", self.text)
        self.assertIn("pending.index==33", self.text)
        self.assertIn("0x1bf34+2*33", self.text)

    def test_native_bank_lookup_verification(self):
        self.assertIn("memory.registerexec(0xbf0a", self.text)
        self.assertIn("memory.registerexec(0xee1c", self.text)
        self.assertIn("f0 dictionary pointer matches", self.text)

    def test_rom_check_is_diagnostic_not_binary_failure(self):
        self.assertIn("fingerprint inconclusive", self.text)
        self.assertIn("rom api unavailable", self.text)
        self.assertIn("fixedjsr", self.text)
        self.assertIn("emu.registerexit(report)", self.text)


if __name__ == "__main__":
    unittest.main()
