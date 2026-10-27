-- Square no Tom Sawyer v29: READ-ONLY Bank6 control/pagination witness.
-- Use with the already visually approved v27 patched ROM, at the CURRENT
-- gameplay position. Does not patch memory, change saves, or press buttons.
-- This collects observations only; it does NOT label 01 or 02 as a verified
-- page-advance command. On-screen text and [BR] draft tokens are separate data.

local OUT = 'SquareTomSawyer_v29_pagination_witness.txt'
local start_frame = emu.framecount()
local last_report = -99999
local MAX_EVENTS = 320
local events, seen = {}, {}
local dispatches = 0
local control_counts = { [0]=0, [1]=0, [2]=0, [3]=0 }
local native_tokens, english_tokens = 0, 0
local secondary_hits = 0
local rom_status = 'unknown'
local function hex(value, digits)
  if type(value) ~= 'number' then return '????' end
  return string.format('%0'..digits..'X',value)
end
local function safe_cpu(at)
  local ok,value = pcall(memory.readbyte,at)
  if ok and type(value)=='number' then return value end
  return nil
end
local function word(at)
  local lo,hi = safe_cpu(at),safe_cpu(at+1)
  if lo == nil or hi == nil then return nil end
  return lo + hi*256
end
local function safe_rom(at)
  if not rom or type(rom.readbyte) ~= 'function' then return nil end
  local ok,value = pcall(rom.readbyte,at)
  if ok and type(value)=='number' then return value end
  return nil
end
local function fingerprint()
  -- v27 unchanged: fixed dispatcher, helper call, B6-356 translated body.
  local checks = {
    {0x3EDF7,0xC9},{0x3EDF8,0xD0},
    {0x3EE1A,0x20},{0x3EE1B,0x0A},{0x3EE1C,0xBF},
    {0x1B870,0xEF},{0x1B871,0x02},{0x1B872,0x01},
    {0x1B873,0xED},{0x1B874,0x01},{0x1B875,0xEE},
  }
  for _,pair in ipairs(checks) do
    if safe_rom(pair[1]) ~= pair[2] then
      rom_status = 'v27 NOT confirmed (or ROM API unavailable)'
      return
    end
  end
  rom_status = 'v27 physical bytes confirmed'
end
local function compact_state()
  return string.format(
    'F5=%s F7=%s F1=%s 7980=%s 7981=%s',
    hex(word(0xF5),4),hex(word(0xF7),4),
    hex(safe_cpu(0xF1),2),hex(safe_cpu(0x7980),2),
    hex(safe_cpu(0x7981),2))
end
local function capture(name, value)
  if #events >= MAX_EVENTS then return end
  local frame=emu.framecount()
  local state=compact_state()
  -- Deduplicate only genuinely identical events in the same frame.
  local key=table.concat({frame,name,value or 0,state},':')
  if seen[key] then return end
  seen[key]=true
  events[#events+1]=string.format(
    'event=%03d frame=%d %s=%s %s',#events+1,frame,name,
    hex(value,2),state)
end
local function report()
  local ok,file=pcall(io.open,OUT,'w')
  if not ok or not file then return end
  file:write('Square no Tom Sawyer - v29 READ-ONLY control witness\n')
  file:write('Source: ',rom_status,'\n')
  file:write('Frames: ',emu.framecount()-start_frame,'\n')
  file:write('EDE7 dispatches: ',dispatches,'\n')
  file:write('01 candidates: ',control_counts[1],'\n')
  file:write('02 candidates: ',control_counts[2],'\n')
  file:write('00 observed: ',control_counts[0],'\n')
  file:write('03 observed: ',control_counts[3],'\n')
  file:write('Native D0-EC tokens: ',native_tokens,'\n')
  file:write('English ED-EF tokens: ',english_tokens,'\n')
  file:write('EE2C secondary-reader entries: ',secondary_hits,'\n')
  file:write('Logged unique control events: ',#events,'\n')
  file:write('Events (CPU pointers are observations, not inferred page state):\n')
  for _,entry in ipairs(events) do file:write(entry,'\n') end
  file:write('Interpretation: 01 and 02 are unclassified until compared\n')
  file:write('against screen transitions and native branch/control logic.\n')
  file:write('No game state, save state, ROM, RAM or input was modified.\n')
  file:close()
  last_report=emu.framecount()
end
fingerprint()
memory.registerexec(0xEDE7,function()
  dispatches=dispatches+1
  local token=memory.getregister('a')
  if type(token)~='number' then return end
  if token>=0 and token<=3 then
    control_counts[token]=control_counts[token]+1
    capture('DISPATCH',token)
  elseif token>=0xD0 and token<=0xEC then
    native_tokens=native_tokens+1
  elseif token>=0xED and token<=0xEF then
    english_tokens=english_tokens+1
  end
end)
memory.registerexec(0xEE2C,function()
  secondary_hits=secondary_hits+1
end)
emu.registerexit(report)
report()
while true do
  local frame=emu.framecount()
  gui.text(2,2,'STS v29 READ-ONLY - control witness')
  gui.text(2,12,'ROM: '..rom_status)
  gui.text(2,22,string.format('01:%d  02:%d  03:%d',control_counts[1],control_counts[2],control_counts[3]))
  gui.text(2,32,string.format('Dispatch:%d  events:%d  English:%d',dispatches,#events,english_tokens))
  if frame-last_report>=120 then report() end
  emu.frameadvance()
end
