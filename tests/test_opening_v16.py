"""Source-free v1.6 first-cutscene pointer relocation tests."""
import sys,unittest,hashlib,struct
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_opening_v16 as v
from english_codec_v15 import encode,decode,CHAR_TO_BYTE

class OpeningTests(unittest.TestCase):
    def setUp(self):
        self.original=bytearray(v.SOURCE_LEN)
        at=v.TEXT_START
        for i,length in enumerate((39,38,26,21,38,16,35,15,24,18,26,37)):
            struct.pack_into('<H',self.original,v.TABLE+2*i,0x8000+at-v.BANK8)
            self.original[at:at+length]=b'\x33'*(length-1)+b'\x00'
            at+=length
        struct.pack_into('<H',self.original,v.TABLE+24,0x8000+at-v.BANK8)
        self.original=bytes(self.original)
        self.sha=hashlib.sha256(self.original).hexdigest()
    def make(self):
        with patch.object(v,'ORIGINAL_SHA',self.sha):
            return v.build(self.original)
    def test_corrected_historical_punctuation(self):
        self.assertEqual(CHAR_TO_BYTE["'"],0x88)
        self.assertEqual(CHAR_TO_BYTE['?'],0x8d)
        self.assertEqual(decode(encode("WHAT'S THAT TOWN?").data),"WHAT'S THAT TOWN?")
    def test_twelve_records_fit(self):
        fw,rb,m=self.make()
        self.assertEqual(m['edited_records'],12)
        self.assertEqual(m['moved_pointers'],10)
        self.assertEqual((m['capacity_bytes'],m['encoded_bytes'],m['free_padding_bytes']),(333,324,9))
        self.assertEqual((len(fw),len(rb)),(832,832))
    def test_exact_original_rollback(self):
        fw,rb,m=self.make()
        after=v.apply_ips(self.original,fw)
        self.assertEqual(v.apply_ips(after,rb),self.original)
        self.assertEqual(hashlib.sha256(after).hexdigest(),m['patched_sha256'])
    def test_correct_english_boundaries(self):
        fw,rb,m=self.make()
        after=v.apply_ips(self.original,fw)
        for i,line in enumerate(v.TEXTS):
            at=v.BANK8+struct.unpack_from('<H',after,v.TABLE+2*i)[0]-0x8000
            self.assertEqual(after[at:at+len(encode(line).data)],encode(line).data)
    def test_later_dialogue_and_header_unchanged(self):
        fw,rb,m=self.make()
        after=v.apply_ips(self.original,fw)
        self.assertEqual(after[:16],self.original[:16])
        self.assertEqual(after[v.TEXT_END:],self.original[v.TEXT_END:])
        self.assertEqual(after[v.TABLE+24:v.TABLE+26],self.original[v.TABLE+24:v.TABLE+26])
    def test_edit_whitelist(self):
        fw,rb,m=self.make();after=v.apply_ips(self.original,fw)
        allowed=set(range(v.TEXT_START,v.TEXT_END))|set(range(v.TABLE,v.TABLE+24))
        for c in v.ALPHABET:
            a=0x17710+v.ALPHABET[c]*8;allowed.update(range(a,a+8))
        for c in v.PUNCT_BITMAPS:
            a=0x17710+v.PUNCTUATION[c]*8;allowed.update(range(a,a+8))
        self.assertFalse({i for i,(a,b) in enumerate(zip(self.original,after)) if a!=b}-allowed)
    def test_wrong_source_refused(self):
        with self.assertRaises(ValueError):v.build(self.original)
    def test_bad_pointer_refused(self):
        bad=bytearray(self.original);struct.pack_into('<H',bad,v.TABLE+2,0x8000)
        with patch.object(v,'ORIGINAL_SHA',hashlib.sha256(bad).hexdigest()):
            with self.assertRaisesRegex(ValueError,'pointer layout'):v.build(bytes(bad))
    def test_bad_record_terminator_refused(self):
        bad=bytearray(self.original);bad[v.TEXT_START]=0
        with patch.object(v,'ORIGINAL_SHA',hashlib.sha256(bad).hexdigest()):
            with self.assertRaisesRegex(ValueError,'interior null'):v.build(bytes(bad))
    def test_overflow_refused(self):
        with patch.object(v,'ORIGINAL_SHA',self.sha),patch.object(v,'TEXTS',tuple(['THIS LINE FITS, YES.\nTHIS LINE FITS, YES.']*12)):
            with self.assertRaisesRegex(ValueError,'overflow'):v.build(self.original)
    def test_unsupported_glyph_refused(self):
        with patch.object(v,'ORIGINAL_SHA',self.sha),patch.object(v,'TEXTS',tuple(['HI—THERE']+list(v.TEXTS[1:]))):
            with self.assertRaisesRegex(ValueError,'Unsupported glyph'):v.build(self.original)

if __name__=='__main__':unittest.main()
