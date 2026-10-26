-- Square no Tom Sawyer v26b: READ-ONLY live bank & dictionary witness.
-- Run with the EXISTING v26 experimental ROM. NO NEW IPS.
-- Distinguishes an ordinary mapped Bank14 byte $09 at $BF0A from the
-- expected executable Bank6 helper beginning $8C at $BF0A.
-- No RAM, ROM, savestate, controller, or game-state writes.

local OUTPUT='SquareTomSawyer_v26b_live_bank_trace.txt'
local start_frame=emu.framecount()
local last_report=-99999
local rom_status='unchecked'
local idle_cpu_helper='unchecked'
local counts={dispatch=0, tokens=0, helper_hits=0, helper_verified=0,
              foreign_bank_hits=0, table_verified=0, table_wrong=0,
              secondary=0, new_english=0}
local observations={}
local observed_tokens={}
local pending={}
local MAX_EVENTS=48
local ROM_BASE=0x18010
local HELPER_CPU=0xBF0A
local TABLE_CPU=0xBF24
local HELPER_FILE=0x1BF1A
local TABLE_FILE=0x1BF34
local helper={0x8C,0x81,0x79,0x8D,0x82,0x79,0x0E,0x81,0x79,
              0x2E,0x82,0x79,0xAD,0x81,0x79,0x18,0x69,0x24,0xA8,
              0xAD,0x82,0x79,0x69,0xBF,0x60,0xEA}
local fixed={
 {0xEDE7,{0xC9,0xD0,0x90,0x06}},
 {0xEDFD,{0x38,0xE9,0xCF,0x85,0xF1,0xA9,0,0x85,0xF2}},
 {0xEE0A,{0x20,0x0A,0xBF}}
}
local function hex2(n) return string.format('%02X',n or 0) end
local function hex4(n) return string.format('%04X',n or 0) end
local function note(message)
 if #observations<MAX_EVENTS then observations[#observations+1]=message end
end
local function read_safe(reader,address)
 local ok,value=pcall(reader,address)
 if ok and type(value)=='number' then return value end
 return nil
end
local function cpu_byte(address) return read_safe(memory.readbyte,address) end
local function cart_byte(address)
 if not rom or type(rom.readbyte)~='function' then return nil end
 return read_safe(rom.readbyte,address)
end
local function physical_from_cpu(address)
 if address>=0xC000 then return 0x3C010+address-0xC000 end
 return ROM_BASE+address-0x8000
end
local function source_matches()
 for _,pair in ipairs(fixed) do
  for i,byte in ipairs(pair[2]) do
   if cart_byte(physical_from_cpu(pair[1]+i-1))~=byte then return false end
  end
 end
 for i,byte in ipairs(helper) do
  if cart_byte(HELPER_FILE+i-1)~=byte then return false end
 end
 return true
end
local function inspect()
 if source_matches() then rom_status='v26 verified'
 elseif rom and type(rom.readbyte)=='function' then rom_status='not v26 or different ROM'
 else rom_status='ROM API unavailable' end
 local value=cpu_byte(HELPER_CPU)
 if value==nil then idle_cpu_helper='unavailable'
 elseif value==0x8C then idle_cpu_helper='Bank6-looking ($8C)'
 elseif value==0x09 then idle_cpu_helper='Bank14-looking ($09)'
 else idle_cpu_helper='other ($'..hex2(value)..')' end
end
local function word_ram(at)
 local a,b=cpu_byte(at),cpu_byte(at+1)
 if not a or not b then return nil end
 return a+256*b
end
local function word_rom(at)
 local a,b=cart_byte(at),cart_byte(at+1)
 if not a or not b then return nil end
 return a+256*b
end
local function status()
 if rom_status~='v26 verified' then return 'v26 CARTRIDGE NOT CONFIRMED' end
 if counts.table_verified>0 and counts.helper_verified>0 then
  return 'LIVE BANK6 HELPER + DICTIONARY POINTER VERIFIED'
 end
 if counts.helper_verified>0 then return 'BANK6 HELPER EXECUTED; POINTER CHECK PENDING' end
 if counts.helper_hits>0 then return 'BF0A HIT; WRONG/UNKNOWN BANK AT ENTRY' end
 if counts.tokens>0 then return 'TOKEN READ; HELPER NOT YET VERIFIED' end
 return 'READY; TRIGGER ONE NEARBY LOOK/NPC LINE'
end
local function report()
 local ok,file=pcall(io.open,OUTPUT,'w')
 if not ok or not file then return end
 local function write(...) file:write(...) end
 write('Square Tom Sawyer - v26b LIVE bank mapping & pointer witness\n')
 write('Physical cartridge fingerprint: ',rom_status,'\n')
 write('CPU BF0A during periodic/idle scan: ',idle_cpu_helper,'\n')
 write('Frames observed: ',emu.framecount()-start_frame,'\n')
 write('Bank6 token dispatcher hits: ',counts.dispatch,'\n')
 write('Tokens D0-ED observed: ',counts.tokens,'\n')
 write('BF0A address hook hits: ',counts.helper_hits,'\n')
 write('BF0A confirmed Bank6 helper bytes at hook time: ',counts.helper_verified,'\n')
 write('BF0A wrong/foreign bank at hook time: ',counts.foreign_bank_hits,'\n')
 write('Dictionary pointer compared MATCH at EE1C: ',counts.table_verified,'\n')
 write('Dictionary pointer compared MISMATCH at EE1C: ',counts.table_wrong,'\n')
 write('Secondary reader EE2C hits: ',counts.secondary,'\n')
 write('English ED token hits: ',counts.new_english,'\n')
 write('STATUS: ',status(),'\n')
 for token=0xD0,0xED do
  if observed_tokens[token] then
   write(string.format('  token %02X: %d\n',token,observed_tokens[token]))
  end
 end
 write('First significant events:\n')
 for _,entry in ipairs(observations) do write(entry,'\n') end
 write('IMPORTANT: $09 at idle BF0A may be another mapped PRG bank; only the\n')
 write('helper-hook-time bytes and EE1C lookup value establish correct execution.\n')
 write('Visual rendering of a genuinely new English phrase remains unverified.\n')
 file:close();last_report=emu.framecount()
end
inspect()

memory.registerexec(0xEDE7,function()
 counts.dispatch=counts.dispatch+1
 local token=memory.getregister('a')
 if token>=0xD0 and token<=0xED then
  counts.tokens=counts.tokens+1
  observed_tokens[token]=(observed_tokens[token] or 0)+1
  if token==0xED then counts.new_english=counts.new_english+1 end
  local primary=word_ram(0xF5)
  note(string.format('frame=%d DISPATCH token=%02X primary_next=%s',
      emu.framecount(),token,primary and hex4(primary) or 'unknown'))
 end
end)
memory.registerexec(0xBF0A,function()
 counts.helper_hits=counts.helper_hits+1
 local matches=true
 local mismatch=nil
 for i,expected in ipairs(helper) do
  local actual=cpu_byte(HELPER_CPU+i-1)
  if actual~=expected then
   matches=false;mismatch=string.format('%04X=%s expected=%02X',
    HELPER_CPU+i-1,actual and hex2(actual) or '??',expected)
   break
  end
 end
 local index=cpu_byte(0xF1) -- patched resolver: index = token - $CF
 if matches then counts.helper_verified=counts.helper_verified+1
 else counts.foreign_bank_hits=counts.foreign_bank_hits+1 end
 pending={index=index,frame=emu.framecount(),valid=matches}
 note(string.format('frame=%d BF0A helper=%s index=%s op=%s',
      emu.framecount(),matches and 'BANK6-VALID' or 'NOT-BANK6',
      index and tostring(index) or 'unknown',mismatch or '8C'))
end)
-- EE1C is reached AFTER $F7/$F8 receive a phrase pointer from BF24 table.
memory.registerexec(0xEE1C,function()
 local index=pending.index
 if not index or pending.frame~=emu.framecount() then return end
 if index<1 or index>30 then
  counts.table_wrong=counts.table_wrong+1
  note('EE1C index outside 1..30: '..tostring(index))
 else
  local expected=word_rom(TABLE_FILE+2*index)
  local actual=word_ram(0xF7)
  local matched=(expected~=nil and actual~=nil and expected==actual and pending.valid)
  if matched then counts.table_verified=counts.table_verified+1
  else counts.table_wrong=counts.table_wrong+1 end
  note(string.format('frame=%d EE1C index=%d ptr=%s expected=%s result=%s',
      emu.framecount(),index,actual and hex4(actual) or 'unknown',
      expected and hex4(expected) or 'unknown',matched and 'MATCH' or 'MISMATCH'))
 end
 pending={}
end)
memory.registerexec(0xEE2C,function() counts.secondary=counts.secondary+1 end)
emu.registerexit(report)
report()
while true do
 local elapsed=emu.framecount()-start_frame
 if elapsed>0 and elapsed%60==0 then inspect() end
 gui.text(2,2,'STS v26b - '..(rom_status=='v26 verified' and 'v26 ROM OK' or 'ROM ?'))
 gui.text(2,12,string.format('tokens %d helper OK %d table OK %d',counts.tokens,
          counts.helper_verified,counts.table_verified))
 gui.text(2,22,'CPU BF0A idle: '..idle_cpu_helper)
 gui.text(2,32,status())
 if elapsed>0 and emu.framecount()-last_report>=120 then report() end
 emu.frameadvance()
end
