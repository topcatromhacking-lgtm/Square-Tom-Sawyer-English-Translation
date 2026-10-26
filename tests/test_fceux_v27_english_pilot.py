"""v27 read-only Lua/actual-private-ROM callback smoke; proprietary ROM is not in repo."""
import hashlib,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from analyze_rom import read_source
import accessible_english_pilot_v27 as v27
SRC=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')
LUA=ROOT/'tools'/'fceux_v27_english_pilot_trace.lua'

class Tests(unittest.TestCase):
    def test_read_only_and_pilot_specific(self):
        s=LUA.read_text(encoding='utf-8')
        for x in ('memory.writebyte(', 'memory.setregister(', 'joypad.set(',
                  'rom.writebyte(', 'savestate.save(', 'emu.loadrom('):
            self.assertNotIn(x,s)
        for x in ('PILOT_FILE+i-1','index>32','TABLE_FILE+64',
                  'SquareTomSawyer_v27_english_phrase_trace.txt'):
            self.assertIn(x,s)

    @unittest.skipUnless(SRC.exists() and shutil.which('texlua'),
                         'Commercial original ROM or Lua unavailable in CI')
    def test_three_phrases_under_actual_patched_rom_mock(self):
        original=read_source(SRC)
        fw,_,report=v27.build(original)
        patched=v27.v23.v16.apply_ips(original,fw)
        self.assertEqual(hashlib.sha256(patched).hexdigest(),report['patched_sha256'])
        with tempfile.TemporaryDirectory() as work:
            d=Path(work);rom=d/'v27.nes';rom.write_bytes(patched)
            fixture=r'''
local cb={};local frame=0;local bank=14;local accumulator=0;local ram={}
local f=assert(io.open([[__ROM__]],'rb'))
local b=assert(f:read('*a'));f:close()
local function cartridge(off)return b:byte(off+1) or 0 end
rom={readbyte=cartridge}
local function read(at)
 if at>=0xC000 then return cartridge(0x3C010+at-0xC000) end
 if at>=0x8000 then return cartridge(0x10+bank*0x4000+at-0x8000) end
 return ram[at] or 0
end
memory={readbyte=read, getregister=function()return accumulator end,
 registerexec=function(at,fn)cb[at]=fn end}
local function word(at,v)ram[at]=v%256;ram[at+1]=math.floor(v/256) end
word(0xF5,0xB861)
local function one(token,index)
 bank=6;accumulator=token;cb[0xEDE7]()
 ram[0xF1]=index
 word(0xF7,cartridge(0x1BF34+2*index)+256*cartridge(0x1BF35+2*index))
 cb[0xBF0A]();cb[0xEE1C]();cb[0xEE2C]();bank=14
end
gui={text=function()end}
emu={framecount=function()return frame end,
 registerexit=function(fn)cb.exit=fn end,
 frameadvance=function()
  frame=frame+1
  if frame==101 then one(0xEF,32) end
  if frame==110 then one(0xED,30) end
  if frame==119 then one(0xEE,31) end
  if frame>170 then error('DONE') end
 end}
local ok,err=pcall(dofile,[[__LUA__]])
assert(not ok and tostring(err):find('DONE'),tostring(err))
cb.exit()
local f2=assert(io.open('SquareTomSawyer_v27_english_phrase_trace.txt','rb'))
local report=f2:read('*a');f2:close()
assert(report:find('Physical cartridge fingerprint: v27 verified'),report)
assert(report:find('New English ED/EE/EF token hits: 3'),report)
assert(report:find('BF0A confirmed Bank6 helper bytes at hook time: 3'),report)
assert(report:find('Dictionary pointer compared MATCH at EE1C: 3'),report)
assert(report:find('THREE ENGLISH PHRASE TOKENS EXECUTED'),report)
print('PASS: v27 source ROM 3-token FCEUX Lua callback simulation')
'''
            script=d/'mock.lua'
            script.write_text(fixture.replace('__ROM__',rom.as_posix())
                                     .replace('__LUA__',LUA.as_posix()),encoding='utf8')
            proc=subprocess.run(['texlua','--luaonly',str(script)],cwd=d,
                                capture_output=True,text=True,timeout=15)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
if __name__=='__main__':unittest.main()
