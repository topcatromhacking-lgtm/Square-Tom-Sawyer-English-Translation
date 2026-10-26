"""Source-only runtime mock and read-only safeguards for v26 FCEUX observer."""
import shutil,subprocess,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
SCRIPT=BASE/'tools'/'fceux_v26_independent_dictionary_trace.lua'

class TraceTests(unittest.TestCase):
    def test_source_read_only(self):
        s=SCRIPT.read_text(encoding='utf8')
        for forbidden in ('memory.writebyte(', 'memory.setregister(', 'rom.writebyte(',
                          'savestate.save(', 'joypad.set(', 'memory.registerwrite('):
            self.assertNotIn(forbidden,s)
        for key in ('0xBF0A','0xEDE7','0xEE2C','SquareTomSawyer_v26_dictionary_trace.txt'):
            self.assertIn(key,s)
    @unittest.skipUnless(shutil.which('texlua'),'texlua missing')
    def test_mock_live_old_token_uses_new_helper(self):
        with tempfile.TemporaryDirectory() as root:
            code=r'''
local callbacks={};local frames=0
local bytes={}
local function put(at,seq)for i=1,#seq do bytes[at+i-1]=seq[i] end end
put(0xEE0A,{0x20,0x0A,0xBF})
put(0xEDE7,{0xC9,0xD0,0x90,0x06})
put(0xEDFD,{0x38,0xE9,0xCF,0x85,0xF1,0xA9,0x00,0x85,0xF2})
put(0xBF0A,{0x8C,0x81,0x79,0x8D,0x82,0x79,0x0E,0x81,0x79,
             0x2E,0x82,0x79,0xAD,0x81,0x79,0x18,0x69,0x24,0xA8,
             0xAD,0x82,0x79,0x69,0xBF,0x60,0xEA})
memory={readbyte=function(at) if frames<70 then return 0 end return bytes[at] or 0 end,
        registerexec=function(at,fn)callbacks[at]=fn end,
        getregister=function(r)assert(r=='a');return 0xD1 end}
rom={readbyte=function(at)
 local cpu=(at>=0x3C010 and 0xC000+(at-0x3C010) or 0x8000+(at-0x18010))
 return bytes[cpu] or 0
end}
gui={text=function(...) end}
emu={framecount=function()return frames end,
 registerexit=function(fn)callbacks.exit=fn end,
 frameadvance=function()
  frames=frames+1
  if frames==90 then callbacks[0xEDE7]();callbacks[0xBF0A]();callbacks[0xEE2C]() end
  if frames>145 then error('INTENTIONAL_STOP') end
 end}
local ok,e=pcall(dofile,[[__SCRIPT_PATH__]])
assert(not ok and tostring(e):find('INTENTIONAL_STOP'),tostring(e))
callbacks.exit()
local f=assert(io.open('SquareTomSawyer_v26_dictionary_trace.txt','r'))
local result=f:read('*a');f:close()
assert(result:find('Accepted v26 fingerprint: true'))
assert(result:find('Single%-byte tokens seen D0%-ED: 1'))
assert(result:find('Independent helper BF0A executions: 1'))
assert(result:find('INDEPENDENT DICTIONARY LOOKUP EXECUTED'))
print('PASS v26 FCEUX mock')
'''
            script=Path(root)/'mock.lua'
            script.write_text(code.replace('__SCRIPT_PATH__',SCRIPT.as_posix()),encoding='utf8')
            r=subprocess.run(['texlua','--luaonly',str(script)],cwd=root,
                             capture_output=True,text=True,timeout=15)
            self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
            self.assertIn('PASS v26 FCEUX mock',r.stdout)
if __name__=='__main__':unittest.main()
