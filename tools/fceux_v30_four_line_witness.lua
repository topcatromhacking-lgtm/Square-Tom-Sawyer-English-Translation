-- Square no Tom Sawyer v30: READ-ONLY English fourth-line pagination witness.
-- Run on v30 standalone cumulative diagnostic IPS (clean Japanese ROM).
-- No save/RAM/ROM/controller mutations, no savestate changes.
local OUTPUT='SquareTomSawyer_v30_four_line_witness.txt'
local started=emu.framecount()
local last_report=-9999
local MAX=96
local events={}
local dispatches, f0_hits, native=0,0,0
local controls={[0]=0,[1]=0,[2]=0,[3]=0}
local helper_hits, helper_ok, ptr_ok, ptr_bad=0,0,0,0
local pending={}
local rom_detail={}
local rom_status='unverified'
local MAPPED_START=0xB860
local physical_start=0x1B870
local pilot={0xEF,0x02,0x01,0xED,0x01,0xEE,0x02,0x01,0xF0,0x00}
local helper={0x8C,0x81,0x79,0x8D,0x82,0x79,0x0E,0x81,0x79,
 0x2E,0x82,0x79,0xAD,0x81,0x79,0x18,0x69,0x24,0xA8,
 0xAD,0x82,0x79,0x69,0xBF,0x60,0xEA}
local function h(n,w)
 if type(n)~='number' then return 'NA' end
 return string.format('%0'..(w or 2)..'X',n)
end
local function read(fn,at)
 if type(fn)~='function' then return nil end
 local ok,value=pcall(fn,at)
 if ok and type(value)=='number' then return value end
 return nil
end
local function cpu(at) return read(memory.readbyte,at) end
local function cart(at)
 if not rom then return nil end
 return read(rom.readbyte,at)
end
local function word_cpu(at)
 local a,b=cpu(at),cpu(at+1)
 if a==nil or b==nil then return nil end
 return a+b*256
end
local function word_cart(at)
 local a,b=cart(at),cart(at+1)
 if a==nil or b==nil then return nil end
 return a+b*256
end
local function fingerprint()
 rom_detail={}
 local checks={{0x3EDF7,0xC9},{0x3EDF8,0xD0},
 {0x3EE1A,0x20},{0x3EE1B,0x0A},{0x3EE1C,0xBF}}
 for i,value in ipairs(pilot) do
  checks[#checks+1]={physical_start+i-1,value}
 end
 local missing,mismatch=0,0
 for _,entry in ipairs(checks) do
  local actual=cart(entry[1])
  if actual==nil then missing=missing+1
  elseif actual~=entry[2] then mismatch=mismatch+1 end
  if (actual==nil or actual~=entry[2]) and #rom_detail<20 then
   rom_detail[#rom_detail+1]=string.format('ROM at %05X got=%s expected=%02X',
      entry[1],h(actual),entry[2])
  end
 end
 local fixed_ok=cpu(0xEE0A)==0x20 and cpu(0xEE0B)==0x0A and cpu(0xEE0C)==0xBF
 if missing==#checks then
  rom_status='ROM API unavailable; fixed-CPU JSR='..(fixed_ok and 'OK' or 'different')
 elseif missing==0 and mismatch==0 then
  rom_status='v30 physical bytes verified'
 else
  rom_status=string.format('v30 fingerprint inconclusive: missing=%d diff=%d fixedJSR=%s',
    missing,mismatch,fixed_ok and 'OK' or 'different')
 end
end
local function event(label,code)
 if #events>=MAX then return end
 local f5,f7=word_cpu(0xF5),word_cpu(0xF7)
 events[#events+1]=string.format(
  'frame=%d %-9s byte=%s F5=%s F7=%s F1=%s 7980=%s',
  emu.framecount(),label,h(code),h(f5,4),h(f7,4),
  h(cpu(0xF1)),h(cpu(0x7980)))
end
local function report()
 local ok,file=pcall(io.open,OUTPUT,'w')
 if not ok or not file then return end
 file:write('Square Tom Sawyer v30 - four-line diagnostic / read-only witness\n')
 file:write('Cartridge status: ',rom_status,'\n')
 for _,line in ipairs(rom_detail) do file:write('fingerprint: ',line,'\n') end
 file:write('Frames: ',emu.framecount()-started,'\n')
 file:write('Text dispatches: ',dispatches,'\n')
 file:write('Byte 01: ',controls[1],'  Byte 02: ',controls[2],'\n')
 file:write('Byte 00: ',controls[0],'  Byte 03: ',controls[3],'\n')
 file:write('Token F0 (PAGE FOUR TEST.): ',f0_hits,'\n')
 file:write('Native tokens D0-EC: ',native,'\n')
 file:write('Helper hits: ',helper_hits,'  verified mapped helper: ',helper_ok,'\n')
 file:write('F0 dictionary pointer matches: ',ptr_ok,
  '  mismatches: ',ptr_bad,'\n')
 file:write('New record B6-356 must carry EF 02 01 ED 01 EE 02 01 F0 00.\n')
 file:write('Critical: F0 hit proves decoder execution, NOT that fourth line\n')
 file:write('is visible or that a full window paginates correctly.\n')
 file:write('No memory/controller/save/ROM writes were made.\n')
 for _,entry in ipairs(events) do file:write(entry,'\n') end
 file:close()
 last_report=emu.framecount()
end
fingerprint()
memory.registerexec(0xEDE7,function()
 dispatches=dispatches+1
 local token=memory.getregister('a')
 if type(token)~='number' then return end
 if token>=0 and token<=3 then
  controls[token]=controls[token]+1
  event('control',token)
 elseif token==0xF0 then
  f0_hits=f0_hits+1
  event('new F0',token)
 elseif token>=0xD0 and token<=0xEC then native=native+1 end
end)
memory.registerexec(0xBF0A,function()
 helper_hits=helper_hits+1
 local valid=true
 for i,expected in ipairs(helper) do
  if cpu(0xBF0A+i-1)~=expected then valid=false;break end
 end
 if valid then helper_ok=helper_ok+1 end
 pending={index=cpu(0xF1),frame=emu.framecount(),valid=valid}
end)
memory.registerexec(0xEE1C,function()
 if not pending.index or pending.frame~=emu.framecount() then return end
 if pending.index==33 then
  local expected=word_cart(0x1BF34+2*33)
  local observed=word_cpu(0xF7)
  if expected~=nil and expected==observed and pending.valid then ptr_ok=ptr_ok+1
  else ptr_bad=ptr_bad+1 end
  event('F0 pointer',pending.index)
 end
 pending={}
end)
emu.registerexit(report)
report()
while true do
 local frame=emu.framecount()
 gui.text(2,2,'STS v30 - FOURTH LINE TEST (no writes)')
 gui.text(2,12,'v30: '..rom_status)
 gui.text(2,22,string.format('F0:%d  01:%d  02:%d  pointers:%d/%d',
  f0_hits,controls[1],controls[2],ptr_ok,ptr_bad))
 gui.text(2,32,'Does PAGE FOUR TEST. appear on a new page?')
 if frame-last_report>=120 then report() end
 emu.frameadvance()
end
