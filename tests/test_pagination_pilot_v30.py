#!/usr/bin/env python3
"""v30 test: source-free dictionary repack + optional real original ROM."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pagination_pilot_v30 as v30


class V30Tests(unittest.TestCase):
    def synthetic_v27(self):
        out = bytearray(v30.TAIL_END)
        cursor = v30.OLD_PHRASE_BEGIN
        for index, (_, phrase) in enumerate(v30.EXISTING, 30):
            v30.v27.v26.putword(out, v30.TABLE + 2 * index,
                                 v30.v27.v26.cpu_of(cursor))
            data = v30.dictionary_body(phrase)
            out[cursor:cursor + len(data)] = data
            cursor += len(data)
        return bytes(out)

    def test_english_token_codes_and_control_bytes(self):
        self.assertEqual(v30.FOUR_LINE_BODY,
                         bytes.fromhex("EF 02 01 ED 01 EE 02 01 F0 00"))
        self.assertEqual([t for t, _ in v30.ALL_PHRASES],
                         [0xED, 0xEE, 0xEF, 0xF0])

    def test_repack_preserves_old_target_table(self):
        baseline = self.synthetic_v27()
        result, detail = v30.extend_dictionary(baseline)
        self.assertEqual(result[v30.TABLE:v30.TABLE + 60],
                         baseline[v30.TABLE:v30.TABLE + 60])
        self.assertEqual(detail["preserved_native_targets"], 29)
        self.assertEqual(len(detail["tokens"]), 4)
        self.assertGreater(detail["free_tail_bytes"], 0)
        self.assertEqual(detail["tokens"][-1]["token"], "F0")
        self.assertEqual(
            int(detail["tokens"][0]["cpu_pointer"], 16),
            v30.v27.v26.cpu_of(v30.NEW_PHRASE_BEGIN)
        )

    def test_original_phrase_checks_are_fail_closed(self):
        baseline = bytearray(self.synthetic_v27())
        baseline[v30.OLD_PHRASE_BEGIN] ^= 1
        with self.assertRaises(ValueError):
            v30.extend_dictionary(bytes(baseline))

    def test_overflow_is_rejected(self):
        baseline = self.synthetic_v27()
        with self.assertRaises(ValueError):
            v30.extend_dictionary(baseline, tail_end=v30.NEW_PHRASE_BEGIN + 5)

    def test_optional_real_rom_end_to_end(self):
        import os
        source = os.environ.get("STS_ORIGINAL_ROM")
        if not source:
            self.skipTest("Set STS_ORIGINAL_ROM to user's private exact source ROM")
        from analyze_rom import read_source
        rom = read_source(Path(source))
        forward, reverse, report = v30.build(rom)
        patched = v30.v27.v23.v16.apply_ips(rom, forward)
        self.assertEqual(v30.v27.v23.v16.apply_ips(patched, reverse), rom)
        self.assertEqual(report["primary_game_dialogue_pointer_edits_vs_v27"], 0)
        self.assertFalse(report["runtime_page_semantics_verified"])


if __name__ == "__main__":
    unittest.main()
