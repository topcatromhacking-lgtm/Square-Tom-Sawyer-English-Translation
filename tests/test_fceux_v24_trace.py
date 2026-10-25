"""Source-only validation of the read-only FCEUX v24 token tracer."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LUA = ROOT / 'tools' / 'fceux_v24_token_trace.lua'

class TraceChecks(unittest.TestCase):
    def test_is_observational(self):
        s = LUA.read_text(encoding='utf8')
        self.assertIn('memory.registerexec(0xEDE7', s)
        self.assertIn('memory.registerexec(0xEDFD', s)
        self.assertIn('memory.registerexec(0xEE2C', s)
        for forbidden in ('memory.writebyte(', 'memory.setregister(', 'joypad.set(',
                          'savestate.save(', 'emu.loadrom(', 'memory.registerwrite('):
            self.assertNotIn(forbidden, s)

    def test_decoder_bytes_explicit(self):
        s = LUA.read_text(encoding='utf8')
        self.assertIn('{0xEDE7, {0xC9,0xD0,0x90,0x06}}', s)
        self.assertIn('{0xEDFD, {0x38,0xE9,0xCF,0x85,0xF1,0xA9,0x00,0x85,0xF2}}', s)
        self.assertIn('0xD0, 0xEC', s)
        self.assertIn('INTRO/NO BANK 6 READER HIT YET', s)

    @unittest.skipUnless(shutil.which('texlua'), 'texlua unavailable, FCEUX Lua mock skipped')
    def test_runtime_mock_generates_report(self):
        snippet = r'''
local callbacks={}
local expected={
 [0xEDE7]=0xC9,[0xEDE8]=0xD0,[0xEDE9]=0x90,[0xEDEA]=0x06,
 [0xEDFD]=0x38,[0xEDFE]=0xE9,[0xEDFF]=0xCF,[0xEE00]=0x85,
 [0xEE01]=0xF1,[0xEE02]=0xA9,[0xEE03]=0x00,[0xEE04]=0x85,[0xEE05]=0xF2,
}
local a=0xD0;local frames=0
memory={readbyte=function(addr) return expected[addr] or 0 end,
 registerexec=function(pc,fn) callbacks[pc]=fn end,
 getregister=function(reg) assert(reg=='a');return a end}
gui={text=function() end}
emu={framecount=function() return frames end,
 registerexit=function(fn) callbacks.exit=fn end,
 frameadvance=function()
  if frames==0 then a=0xD0;callbacks[0xEDE7]();callbacks[0xEDFD]();callbacks[0xEE2C]() end
  frames=frames+1
  if frames>4 then error('INTENTIONAL_MOCK_STOP') end
 end}
local ok,err=pcall(dofile, [[__SCRIPT_PATH__]])
assert(not ok and tostring(err):find('INTENTIONAL_MOCK_STOP'))
callbacks.exit()
local f=assert(io.open('SquareTomSawyer_v24_token_trace.txt','r'))
local content=f:read('*a');f:close()
assert(content:find('v23 decoder bytes confirmed'))
assert(content:find('Token candidates D0%-EC: 1'))
assert(content:find('Token resolver EDFD: 1'))
assert(content:find('Secondary reader EE2C: 1'))
assert(content:find('TOKEN PATH EXECUTED'))
print('PASS FCEUX-Lua-mock trace')
'''
        with tempfile.TemporaryDirectory() as td:
            mock = Path(td) / 'mock.lua'
            mock.write_text(snippet.replace('__SCRIPT_PATH__', LUA.as_posix()),encoding='utf-8')
            done = subprocess.run(['texlua','--luaonly', str(mock)],cwd=td,
                                  capture_output=True,text=True,timeout=15)
            self.assertEqual(done.returncode,0,done.stdout+done.stderr)
            self.assertIn('PASS FCEUX-Lua-mock trace',done.stdout)

if __name__=='__main__': unittest.main()
