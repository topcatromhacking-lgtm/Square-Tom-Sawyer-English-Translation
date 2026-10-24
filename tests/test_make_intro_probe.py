"""No commercial ROM needed: IPS format, modification scope and rollback tests."""
import pathlib
import sys
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import make_intro_probe as p

class IntroProbeTests(unittest.TestCase):
    def test_line_format(self):
        self.assertEqual(p.NEW_INTERIOR[:3],bytes.fromhex("70 6A 71"))
        self.assertEqual(len(p.NEW_LINE),len(p.ORIGINAL_LINE))
        self.assertEqual(p.NEW_LINE[0],p.ORIGINAL_LINE[0])
        self.assertEqual(p.NEW_LINE[-1],p.ORIGINAL_LINE[-1])
    def test_ips_roundtrip(self):
        orig=bytes(range(256))*8
        patch=p.ips_make([(0x123,b"ABC")])
        reverse=p.ips_make([(0x123,orig[0x123:0x126])])
        new=p.ips_apply(orig,patch)
        self.assertEqual(new[0x123:0x126],b"ABC")
        self.assertEqual(p.ips_apply(new,reverse),orig)
    def test_reject_bad_record(self):
        for records in [[(0x454F46,b"A")],[(0,b"")],[(0,b"A"),(0,b"B")]]:
            with self.subTest(records=records),self.assertRaises(ValueError):
                p.ips_make(records)
    def test_reject_bad_ips(self):
        with self.assertRaises(ValueError):p.ips_apply(bytes(32),b"BAD")
        with self.assertRaises(ValueError):
            p.ips_apply(bytes(32),b"PATCH"+b"\0\0\x03\0\x08AAA"+b"EOF")
    def test_reject_unverified_source(self):
        with self.assertRaises(Exception):
            p.apply_at_verified_offset(bytes(262160))
    def test_scope_and_pointer(self):
        fake=bytearray(262160)
        fake[p.INTRO_START:p.INTRO_START+13]=p.ORIGINAL_LINE
        fake[p.POINTER_OFFSET:p.POINTER_OFFSET+2]=bytes.fromhex("8F 92")
        with patch.object(p,"get_record_map",return_value=([],{})):
            new=p.apply_at_verified_offset(bytes(fake))
        self.assertEqual(new[p.EDIT_START:p.EDIT_START+11],p.NEW_INTERIOR)
        self.assertEqual(new[:p.INTRO_START],bytes(fake[:p.INTRO_START]))
        self.assertEqual(new[p.INTRO_START+13:],bytes(fake[p.INTRO_START+13:]))

if __name__=="__main__":unittest.main()
