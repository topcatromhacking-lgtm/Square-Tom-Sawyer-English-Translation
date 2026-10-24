import sys,unittest,hashlib,struct
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import relocate_dialogue_v15 as m

class RelocationTests(unittest.TestCase):
    def setUp(self):
        original=bytearray(262160)
        original[0x18812:0x18819]=b'\x00\x00A\x8fB\x8f\x00'
        original[0x18819:0x18824]=b'\x00\x00A\x8fB\x8fC\x8fD\x8f\x00'
        original[0x18824:0x1882d]=b'\x00\x00A\x8fB\x8fC\x8f\x00'
        original[0x1882d:0x18832]=b'\x00\x00B\x8f\x00'
        self.records=[]
        for i,(ptr,text,length) in enumerate([(0x18014,0x18812,7),(0x18016,0x18819,11),
                                                 (0x18018,0x18824,9),(0x1801a,0x1882d,5)]):
            value=0x8000+(text-0x18010)
            struct.pack_into('<H',original,ptr,value)
            self.records.append({'global_index':i,'group':1,'table_file_offset':hex(ptr),
                                 'text_file_offset':hex(text),'length_bytes':length})
        self.original=bytes(original)
    def call(self,*args,**kwargs):
        with patch.object(m,'SHA256',hashlib.sha256(self.original).hexdigest()),\
             patch.object(m,'get_record_map',return_value=(self.records,{})):
            return m.repack_window(self.original,*args,**kwargs)
    def test_noop_repack_is_identical(self):
        r=self.call(1,2,{1:self.original[0x18819:0x18824]})
        self.assertEqual(r.rom,self.original)
    def test_one_pointer_moves_and_all_others_unchanged(self):
        old1=self.original[0x18819:0x18824]
        old2=self.original[0x18824:0x1882d]
        r=self.call(1,3,{1:old1[:-1]+b'\x8f\x00',2:old2[:-2]+b'\x00'},
                    require_pointer_move=True)
        self.assertEqual(len(r.changes),1)
        self.assertEqual(r.changes[0][0],2)
        self.assertEqual(struct.unpack_from('<H',r.rom,0x18018)[0],0x8815)
        self.assertEqual(r.rom[0x18812:0x18819],self.original[0x18812:0x18819])
        self.assertEqual(r.rom[0x1882d:],self.original[0x1882d:])
        self.assertEqual(len(r.rom),len(self.original))
    def test_reject_window_overflow(self):
        with self.assertRaisesRegex(ValueError,'overflow'):
            self.call(0,0,{0:b'\x6e'*20+b'\x00'})
    def test_reject_cross_group(self):
        self.records[2]['group']=2
        with self.assertRaisesRegex(ValueError,'group'):
            self.call(1,2,{1:b'\x00'})
    def test_reject_wrong_rom(self):
        with patch.object(m,'get_record_map',return_value=(self.records,{})):
            with self.assertRaises(ValueError):m.repack_window(self.original,1,2,{1:b'\x00'})
    def test_reject_outside_replacement(self):
        with self.assertRaisesRegex(ValueError,'entirely within'):
            self.call(1,2,{3:b'\x00'})
    def test_reject_missing_terminator(self):
        with self.assertRaisesRegex(ValueError,'ending in 00'):
            self.call(1,2,{1:b'ABC'})
    def test_reject_no_pointer_move_when_required(self):
        with self.assertRaisesRegex(ValueError,'No pointers'):
            self.call(1,2,{1:self.original[0x18819:0x18824]},require_pointer_move=True)
