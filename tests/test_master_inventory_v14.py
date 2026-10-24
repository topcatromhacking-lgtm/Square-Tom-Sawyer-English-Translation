import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_master_inventory_v14 import extract_candidates,lower_bound_bytes,reconcile

class Tests(unittest.TestCase):
    def fixture(self):
        return [{'global_index':0,'group':1,'table_file_offset':'0x18014','cpu_pointer':'0x8802','text_file_offset':'0x18812','length_bytes':11},
                {'global_index':1,'group':1,'table_file_offset':'0x18016','cpu_pointer':'0x880D','text_file_offset':'0x1881D','length_bytes':4}]
    def test_parse_and_end(self):
        text='//POINTER #0 @ $18014 - STRING #0 @ $18812\n#W16($18014)\nテスト[ED]\nEnglish words.\n\n//POINTER #1 @ $1820A - STRING #1 @ $2000F\n#W16($1820A)\n[ED]\n^((Unsure))\n'
        got=extract_candidates(text,'fixture.txt')
        self.assertEqual(len(got),2)
        self.assertEqual(got[0]['english_candidate'],'English words.')
        self.assertEqual(got[1]['english_candidate'],'')
    def test_reconcile_separators(self):
        c=[{'script_file':'x','external_index':1,'pointer_file_offset':0x18014,'text_file_offset':0x18812,'english_candidate':'ENGLISH','end_marker_seen':True},
           {'script_file':'x','external_index':2,'pointer_file_offset':0x1820a,'text_file_offset':0x2000f,'english_candidate':'','end_marker_seen':True}]
        rows,extras,s=reconcile(self.fixture(),c)
        self.assertEqual(s['exact_matches'],1)
        self.assertEqual(s['group_delimiter_entries'],1)
        self.assertEqual(rows[0]['minimum_one_byte_requirement'],8)
        self.assertEqual(rows[1]['match_status'],'NOT_IN_EXTERNAL_SCRIPT')
    def test_offset_mismatch_does_not_silently_match(self):
        c=[{'script_file':'x','external_index':1,'pointer_file_offset':0x18014,'text_file_offset':0x2000f,'english_candidate':'BAD','end_marker_seen':True}]
        rows,extras,s=reconcile(self.fixture(),c)
        self.assertEqual(rows[0]['match_status'],'OFFSET_MISMATCH')
        self.assertEqual(len(extras),1)
    def test_reject_duplicate_pointer(self):
        c=[{'script_file':'x','external_index':i,'pointer_file_offset':0x18014,'text_file_offset':0x18812,'english_candidate':'YES','end_marker_seen':True} for i in (1,2)]
        rows,extras,s=reconcile(self.fixture(),c)
        self.assertEqual(rows[0]['match_status'],'DUPLICATE_REFERENCE')
        self.assertEqual(len(extras),2)
    def test_lower_bounds(self):
        self.assertIsNone(lower_bound_bytes(''))
        self.assertEqual(lower_bound_bytes('HI'),3)
        self.assertEqual(lower_bound_bytes('ONE NIGHT'),10)

if __name__=='__main__':unittest.main()
