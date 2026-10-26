-- v26 READ-ONLY FCEUX: independent 30-entry Bank6 dictionary runtime probe.
-- Attach to the v26 experimental cumulative IPS (never stack with v23).
-- Does not write ROM, RAM, saves or controller state.

local OUT='SquareTomSawyer_v26_dictionary_trace.txt'
local frame0=emu.framecount()
local lastsave=-9999
local accepted=false
local cpu_state='pending'
local rom_state='pending'
local counts={dispatcher=0,tokens=0,lookup=0,reader=0,english=0}
local observed={}
local log={}
local MAX=48
local function add(x)
 if #log<MAX then log[#log+1]=x end
end
local wanted={
 {0xEE0A,{0x20,0x0A,0xBF}}, -- v26 JSR newly relocated helper
 {0xEDE7,{0xC9,0xD0,0x90,0x06}}, -- v23/v26 one-byte dispatch
 {0xEDFD,{0x38,0xE9,0xCF,0x85,0xF1,0xA9,0,0x85,0xF2}},
}
local helper={0x8C,0x81,0x79,0x8D,0x82,0x79,0x0E,0x81,0x79,
 0x2E,0x82,0x79,0xAD,0x81,0x79,0x18,0x69,0x24,0xA8,
 0xAD,0x82,0x79,0x69,0xBF,0x60,0xEA}
local function safe(reader,addr)
 local ok,val=pcall(reader,addr)
 if ok and type(val)=='number' then return val end
 return nil
end
local function match(readcpu)
 for _,pair in ipairs(wanted) do
  for i=1,#pair[2] do
   local value=readcpu(pair[1]+i-1)
   if value==nil then return 'unavailable' end
   if value~=pair[2][i] then
    if value==0 then return 'unmapped / zero' end
    return string.format('other (%04X=%02X)',pair[1]+i-1,value)
   end
  end
 end
 for i=1,#helper do
  local value=readcpu(0xBF0A+i-1)
  if value==nil then return 'unavailable' end
  if value~=helper[i] then
   if value==0 then return 'Bank6 helper unmapped' end
   return string.format('wrong Bank6 helper (%04X=%02X)',0xBF0A+i-1,value)
  end
 end
 return 'v26'
end
local function inspect()
 if type(rom)=='table' and type(rom.readbyte)=='function' then
  rom_state=match(function(cpu)
   local file = cpu>=0xC000 and (0x3C010+cpu-0xC000)
      or (0x18010+cpu-0x8000)
   return safe(rom.readbyte,file)
  end)
 else rom_state='unavailable' end
 cpu_state=match(function(cpu) return safe(memory.readbyte,cpu) end)
 accepted=(rom_state=='v26' or cpu_state=='v26')
end
local function status()
 if not accepted then return 'v26 PATCH NOT CONFIRMED YET' end
 if counts.lookup>0 and counts.tokens>0 then
  return 'INDEPENDENT DICTIONARY LOOKUP EXECUTED'
 end
 if counts.dispatcher>0 then return 'BANK6 READER ACTIVE; NO TOKEN LOOKUP YET' end
 return 'READY; TRIGGER ONE NEARBY LOOK/NPC TEXT'
end
local function write_report()
 local ok,f=pcall(io.open,OUT,'w')
 if not ok or not f then return end
 f:write('Square Tom Sawyer - v26 independent dictionary runtime trace\n')
 f:write('ROM file signature: ',rom_state,'\n')
 f:write('Mapped CPU signature: ',cpu_state,'\n')
 f:write('Accepted v26 fingerprint: ',tostring(accepted),'\n')
 f:write('Frames: ',emu.framecount()-frame0,'\n')
 f:write('Bank6 main text dispatches: ',counts.dispatcher,'\n')
 f:write('Single-byte tokens seen D0-ED: ',counts.tokens,'\n')
 f:write('Independent helper BF0A executions: ',counts.lookup,'\n')
 f:write('Secondary reader EE2C executions: ',counts.reader,'\n')
 f:write('New English token ED executions: ',counts.english,'\n')
 f:write('STATUS: ',status(),'\n')
 for b=0xD0,0xED do
  if observed[b] then f:write(string.format('  Token $%02X: %d hits\n',b,observed[b])) end
 end
 f:write('First events:\n')
 for _,msg in ipairs(log) do f:write(msg,'\n') end
 f:write('New token ED is in the B6-420 diagnostic entry; it may be inaccessible nearby.\n')
 f:write('Old D1/DD token activity also proves the independent helper is callable.\n')
 f:write('Execution count does not prove displayed glyph accuracy.\n')
 f:close()
 lastsave=emu.framecount()
end
inspect()
memory.registerexec(0xEDE7,function()
 if not accepted then return end
 counts.dispatcher=counts.dispatcher+1
 local a=memory.getregister('a')
 if a>=0xD0 and a<=0xED then
  counts.tokens=counts.tokens+1;observed[a]=(observed[a] or 0)+1
  if a==0xED then counts.english=counts.english+1 end
  add(string.format('frame %d token $%02X',emu.framecount(),a))
 end
end)
memory.registerexec(0xBF0A,function()
 if accepted then
  counts.lookup=counts.lookup+1
  add(string.format('frame %d independent helper entered',emu.framecount()))
 end
end)
memory.registerexec(0xEE2C,function()
 if accepted then counts.reader=counts.reader+1 end
end)
emu.registerexit(write_report)
write_report()
while true do
 local elapsed=emu.framecount()-frame0
 if elapsed>0 and elapsed%60==0 then inspect() end
 gui.text(2,2,'STS v26 lookup: '..(accepted and 'MATCH' or 'UNCONFIRMED'))
 gui.text(2,12,string.format('dispatch %d, tokens %d, BF0A calls %d',counts.dispatcher,counts.tokens,counts.lookup))
 gui.text(2,22,'ROM: '..rom_state)
 gui.text(2,32,status())
 if elapsed>0 and emu.framecount()-lastsave>=120 then write_report() end
 emu.frameadvance()
end
