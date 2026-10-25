import sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decoder_hook_survey_v22 import audit
ROM=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')
class Pure(unittest.TestCase):
    def test_reject_bad_rom(self):
        with self.assertRaises(ValueError):audit(b'')
@unittest.skipUnless(ROM.exists(),'Commercial source ROM not installed')
class WithRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROM) as z:cls.rom=z.read('Square no Tom Sawyer (Japan).nes')
    def test_known_callers_and_native_dispatch(self):
        r=audit(self.rom)
        self.assertEqual(r['fixed_bank_raw_opcode_occurrences']['JSR_EDC2'],['CB9F'])
        self.assertEqual(r['fixed_bank_raw_opcode_occurrences']['JMP_EDC2'],['C057'])
        self.assertEqual(r['fixed_bank_raw_opcode_occurrences']['JSR_EE50'],['ED65','EDF1','EE44'])
        self.assertIn('EDCD',r['fixed_bank_raw_opcode_occurrences']['LDA_7980'])
    def test_ff_and_zero_runs_exist_but_not_free(self):
        r=audit(self.rom)
        self.assertTrue(r['ff_runs_at_least_24_bytes'])
        self.assertTrue(r['zero_runs_at_least_24_bytes'])
        self.assertIn('No verified fixed-bank',r['safety_conclusion'])
    def test_mutated_signature_rejected(self):
        b=bytearray(self.rom);b[0x3C010+0xEDE7-0xC000]^=1
        with self.assertRaises(ValueError):audit(bytes(b))
if __name__=='__main__':unittest.main()
