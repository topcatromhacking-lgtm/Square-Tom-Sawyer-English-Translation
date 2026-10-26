"""Read-only v26b live-bank witness. ROM-backed mock is optional in CI."""
import hashlib,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'tools'/'fceux_v26b_live_bank_witness.lua'
SRC=Path('/mnt/data/Square no Tom Sawyer (Japan).zip')
ENGINE=ROOT/'tools'
class WitnessSafetyTests(unittest.TestCase):
    def test_observer_has_no_memory_writes(self):
        s=SCRIPT.read_text()
        for forbidden in ('memory.writebyte(', 'memory.setregister(', 'rom.writebyte(',
                          'savestate.save(', 'joypad.set(', 'memory.registerwrite(',
                          'emu.loadrom('):
            self.assertNotIn(forbidden,s)
        for required in ('memory.registerexec(0xBF0A','memory.registerexec(0xEE1C',
                         'CPU BF0A idle:', 'primary_next=', 'TABLE_FILE+2*index'):
            self.assertIn(required,s)
    @unittest.skipUnless(SRC.exists() and shutil.which('texlua'),
                         'Commercial ROM or Lua unavailable')
    def test_actual_v26_rom_idle_bank14_and_live_bank6(self):
        sys.path.insert(0,str(ENGINE))
        import independent_dictionary_v26 as build
        with zipfile.ZipFile(SRC) as z: original=z.read(z.namelist()[0])
        ips,undo,report=build.compile(original)
        patched=build.v23.v16.apply_ips(original,ips)
        self.assertEqual(hashlib.sha256(patched).hexdigest(),report['patched_sha256'])
        for mode in ('valid','invalid'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp);romfile=folder/'patched.nes';romfile.write_bytes(patched)
                mock=r'''
local callbacks={};local frames=0;local bank=14;local z={}
local f=assert(io.open([[__ROM__]],'rb'));local data=assert(f:read('*a'));f:close()
local function cart(pos)return data:byte(pos+1) or 0 end
rom={readbyte=cart}
local function read(at)
 if at>=0xC000 then return cart(0x3C010+at-0xC000) end
 if at>=0x8000 then return cart(0x10+bank*0x4000+at-0x8000) end
 return z[at] or 0
end
memory={readbyte=read,getregister=function(r)assert(r=='a');return 0xDD end,
 registerexec=function(at,fn)callbacks[at]=fn end}
local function putword(at,w)z[at]=w%256;z[at+1]=math.floor(w/256) end
z[0xF1]=14;putword(0xF5,0x9A10)
local target=cart(0x1BF34+28)+256*cart(0x1BF34+29)
putword(0xF7,target)
gui={text=function(...)end}
emu={framecount=function()return frames end,
 registerexit=function(fn)callbacks.exit=fn end,
 frameadvance=function()
  frames=frames+1
  if frames==101 then
   bank=6;callbacks[0xEDE7]()
   if '__MODE__'=='valid' then bank=6 else bank=14 end
   callbacks[0xBF0A]();callbacks[0xEE1C]();callbacks[0xEE2C]()
   bank=14
  end
  if frames>180 then error('MOCK_STOP') end
 end}
local ok,e=pcall(dofile,[[__SCRIPT__]])
assert(not ok and tostring(e):find('MOCK_STOP'),tostring(e))
callbacks.exit()
local f2=assert(io.open('SquareTomSawyer_v26b_live_bank_trace.txt','rb'))
local t=f2:read('*a');f2:close()
assert(t:find('Physical cartridge fingerprint: v26 verified'),t)
assert(t:find('CPU BF0A during periodic/idle scan: Bank14%-looking %(%$09%)'),t)
if '__MODE__'=='valid' then
 assert(t:find('BF0A confirmed Bank6 helper bytes at hook time: 1'),t)
 assert(t:find('Dictionary pointer compared MATCH at EE1C: 1'),t)
 assert(t:find('LIVE BANK6 HELPER %+' ),t)
else
 assert(t:find('BF0A wrong/foreign bank at hook time: 1'),t)
 assert(t:find('Dictionary pointer compared MISMATCH at EE1C: 1'),t)
end
print('v26b MOCK PASS '..'__MODE__')
'''
                p=folder/'mock.lua'
                p.write_text(mock.replace('__ROM__',romfile.as_posix())
                              .replace('__SCRIPT__',SCRIPT.as_posix())
                              .replace('__MODE__',mode))
                run=subprocess.run(['texlua','--luaonly',str(p)],cwd=tmp,
                                   capture_output=True,text=True,timeout=15)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                self.assertIn('v26b MOCK PASS '+mode,run.stdout)
if __name__=='__main__':unittest.main()
