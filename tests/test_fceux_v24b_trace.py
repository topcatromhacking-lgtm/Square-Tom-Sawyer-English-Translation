"""v24b FCEUX Lua observer: read-only and resilient to delayed CPU mapping."""
from pathlib import Path
import shutil, subprocess, tempfile, unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'tools'/'fceux_v24b_token_trace.lua'

class StaticChecks(unittest.TestCase):
    def test_read_only(self):
        text=SCRIPT.read_text(encoding='utf8')
        for forbidden in ('memory.writebyte(', 'memory.setregister(', 'rom.writebyte(',
                          'joypad.set(', 'savestate.save(', 'memory.registerwrite('):
            self.assertNotIn(forbidden,text)
    def test_rechecks_both_signatures(self):
        text=SCRIPT.read_text(encoding='utf8')
        self.assertIn('rom.readbyte(0x3C010 + pc-0xC000)',text)
        self.assertIn('cpu_state=inspect(memory.readbyte)',text)
        self.assertIn('elapsed%60==0 then rescan()',text)
        self.assertIn('SquareTomSawyer_v24b_token_trace.txt',text)
    @unittest.skipUnless(shutil.which('texlua'),'TeX Lua not available')
    def test_runtime_mock_delayed_cpu_mapping_and_old_rom(self):
        for mode in ('v23','old','unavailable'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as work:
                orig='0xC9,0x03,0xD0,0x06'
                new='0xC9,0xD0,0x90,0x06'
                rom_first=new if mode=='v23' else orig
                source=r'''
local callbacks = {}
local currentFrame = 0
local romBytes = {}
local cpuBytes = {}
local function loadBytes(out,addr,vals)
  for i=1,#vals do out[addr+i-1]=vals[i] end
end
loadBytes(cpuBytes,0xEDE7,{0xC9,0xD0,0x90,0x06})
loadBytes(cpuBytes,0xEDFD,{0x38,0xE9,0xCF,0x85,0xF1,0xA9,0,0x85,0xF2})
loadBytes(romBytes,0xEDE7,{__FIRST__})
loadBytes(romBytes,0xEDFD,__SECOND__)
memory={
 readbyte=function(addr)
   if currentFrame<45 then return 0 end
   if __MODE__=='old' then return romBytes[addr] or 0 end
   return cpuBytes[addr] or 0
 end,
 getregister=function(register) return 0xD0 end,
 registerexec=function(addr,fn) callbacks[addr]=fn end,
}
rom={readbyte=function(off) return romBytes[off-0x3C010+0xC000] or 0 end}
if __MODE__=='unavailable' then rom=nil end
gui={text=function(...) end}
emu={
 framecount=function() return currentFrame end,
 registerexit=function(fn) callbacks.exit=fn end,
 frameadvance=function()
   currentFrame=currentFrame+1
   if currentFrame==74 then
      callbacks[0xEDE7](); callbacks[0xEDFD](); callbacks[0xEE2C]()
   end
   if currentFrame>133 then error('END_OF_MOCK') end
 end
}
local ok,err=pcall(dofile,[[__SCRIPT__]])
assert(not ok and tostring(err):find('END_OF_MOCK'),tostring(err))
callbacks.exit()
local f=assert(io.open('SquareTomSawyer_v24b_token_trace.txt','r'))
local output=f:read('*a');f:close();print(output)
'''
                second=('{0xA9,0,0x85,0xF2,0x20,0x92,0xED,0x85,0xF1}'
                        if mode=='old' else '{0x38,0xE9,0xCF,0x85,0xF1,0xA9,0,0x85,0xF2}')
                text=(source.replace('__FIRST__',rom_first)
                            .replace('__SECOND__',second)
                            .replace('__MODE__',"'" + mode + "'")
                            .replace('__SCRIPT__',SCRIPT.as_posix()))
                path=Path(work)/'mock.lua';path.write_text(text,encoding='utf8')
                result=subprocess.run(['texlua','--luaonly',str(path)],cwd=work,
                    capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if mode=='old':
                    self.assertIn('ROM file decoder bytes: original-unpatched',result.stdout)
                    self.assertIn('Token candidates D0-EC: 0',result.stdout)
                else:
                    self.assertIn('Token candidates D0-EC: 1',result.stdout)
                    self.assertIn('TOKEN PATH EXECUTED',result.stdout)
if __name__=='__main__':unittest.main()
