import sys,unittest,tempfile,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from dte_capacity_v20 import compress,load_bank6_english

class CompressionEstimateTests(unittest.TestCase):
    def test_never_increases_symbols(self):
        r=compress(['HELLO HELLO','HELLO HELLO'],max_tokens=4)
        self.assertEqual(r['records_modeled'],2)
        self.assertLess(r['estimates'][-1]['visible_symbols'],r['characters_before'])
    def test_header_terminator_budget(self):
        r=compress(['ABC',''],max_tokens=0)
        self.assertEqual(r['estimates'][0]['minimum_record_bytes'],3+6)
    def test_invalid_token_budget(self):
        with self.assertRaises(ValueError):compress(['HI'],max_tokens=191)
    def test_does_not_join_across_record_boundaries(self):
        r=compress(['A','B'],max_tokens=10)
        self.assertEqual(r['token_dictionary_entries'],0)
    def test_empty_input(self):
        r=compress([],max_tokens=10)
        self.assertEqual(r['records_modeled'],0)
    def test_strict_tsv_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'fake.tsv';p.write_text('bank\tenglish\n6\tTEST\n',encoding='utf8')
            with self.assertRaises(ValueError):load_bank6_english(p)
if __name__=='__main__':unittest.main()
