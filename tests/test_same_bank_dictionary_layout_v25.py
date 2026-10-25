"""v25 same-Bank6 phrase dictionary capacity model, source-independent."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from same_bank_dictionary_layout_v25 import plan,CAPACITY,TEXT_END

class SameBankTests(unittest.TestCase):
    def test_160_phrase_estimate_fits(self):
        r=plan(encoded_symbols=11075,dictionary_phrase_data_bytes=726,tokens=160)
        self.assertEqual(r['record_bytes'],12512)
        self.assertEqual(r['new_pointer_table_bytes'],320)
        self.assertEqual(r['total_needed_bytes'],13558)
        self.assertEqual(r['margin_bytes'],767)
        self.assertTrue(r['fits_same_bank_in_model'])
        self.assertEqual(r['layout']['padding_bytes'],767)
    def test_144_token_estimate_fits(self):
        r=plan(encoded_symbols=11447,dictionary_phrase_data_bytes=599,tokens=144)
        self.assertEqual(r['margin_bytes'],554)
    def test_176_token_estimate_fits(self):
        r=plan(encoded_symbols=10724,dictionary_phrase_data_bytes=791,tokens=176)
        self.assertEqual(r['margin_bytes'],1021)
    def test_failure_does_not_allocate(self):
        r=plan(encoded_symbols=22996,dictionary_phrase_data_bytes=0,tokens=0)
        self.assertFalse(r['fits_same_bank_in_model'])
        self.assertIsNone(r['layout'])
        self.assertEqual(r['margin_bytes'],-10108)
    def test_overcount_control_line_costs(self):
        r=plan(encoded_symbols=11075+768,dictionary_phrase_data_bytes=726,tokens=160)
        self.assertEqual(r['margin_bytes'],-1)
    def test_pointer_cpu_range(self):
        r=plan(encoded_symbols=11075,dictionary_phrase_data_bytes=726,tokens=160)
        self.assertTrue(int(r['layout']['dictionary_pointer_start_cpu'],16)>=0x8000)
        self.assertLess(int(r['layout']['phrase_data_start_cpu'],16),0xC000)
        self.assertLessEqual(int(r['layout']['phrase_data_end_exclusive_file'],16),TEXT_END)
    def test_invalid_no_phrases(self):
        with self.assertRaises(ValueError):plan(encoded_symbols=2,tokens=160,dictionary_phrase_data_bytes=319)
    def test_invalid_count(self):
        with self.assertRaises(ValueError):plan(encoded_symbols=2,tokens=160,dictionary_phrase_data_bytes=320,records=478)
if __name__=='__main__':unittest.main()
