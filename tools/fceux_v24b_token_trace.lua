-- Square no Tom Sawyer v24b: READ-ONLY FCEUX native token execution tracer.
-- Works with experimental v23 IPS. Does not modify ROM, RAM, savestates or joypad.
-- An English INTRO alone is NOT evidence of v23 Bank 6 token execution.

local OUT = 'SquareTomSawyer_v24b_token_trace.txt'
local D0, EC = 0xD0, 0xEC
local counters = {reads=0, token_candidates=0, bad_high=0,
                  resolver=0, secondary=0, glyph=0}
local token_counts = {}
local observations = {}
local MAX_OBSERVATIONS = 36
local frame_start = emu.framecount()
local last_write = -9999
local last_token = 'none'
local write_problem = false

local expected = {
    {0xEDE7, {0xC9,0xD0,0x90,0x06}},
    {0xEDFD, {0x38,0xE9,0xCF,0x85,0xF1,0xA9,0x00,0x85,0xF2}},
}

-- v24b: independently verify the ROM file and currently mapped CPU bytes.
-- CPU memory may not have PRG mapped when a Lua script first starts.
-- FCEUX rom.readbyte uses *file offsets including the iNES header*.
local original = {
    {0xEDE7, {0xC9,0x03,0xD0,0x06}},
    {0xEDFD, {0xA9,0x00,0x85,0xF2,0x20,0x92,0xED,0x85,0xF1}},
}
local valid, reason = false, 'Waiting for ROM/CPU verification'
local rom_state, cpu_state = 'not checked', 'not checked'
local retries = 0
local function inspect(reader)
    if not reader then return 'unavailable' end
    local seen, total, good, old = 0, 0, true, true
    local first = 'not read'
    for j,pair in ipairs(expected) do
        local start, bytes, before = pair[1],pair[2],original[j][2]
        for i=1,#bytes do
            local ok,value = pcall(reader,start+i-1)
            if not ok or type(value) ~= 'number' then
                return 'unavailable (read error)'
            end
            if seen==0 then first=string.format('%02X',value) end
            seen=seen+1
            total=total+value
            if value~=bytes[i] then good=false end
            if value~=before[i] then old=false end
        end
    end
    if good then return 'v23' end
    if old then return 'original-unpatched' end
    if total==0 then return 'all-zero/unmapped' end
    return 'other (first byte $'..first..')'
end
local function read_cartridge(pc)
    return rom.readbyte(0x3C010 + pc-0xC000)
end
local function rescan()
    retries=retries+1
    if type(rom)=='table' and type(rom.readbyte)=='function' then
        rom_state=inspect(read_cartridge)
    else
        rom_state='unavailable'
    end
    cpu_state=inspect(memory.readbyte)
    valid=(rom_state=='v23' or cpu_state=='v23')
    if valid then
        reason='v23 decoder bytes confirmed (ROM='..rom_state..'; CPU='..cpu_state..')'
    elseif rom_state=='original-unpatched' then
        reason='LOADED ROM FILE IS ORIGINAL/UNPATCHED (CPU='..cpu_state..')'
    elseif cpu_state=='original-unpatched' and rom_state~='v23' then
        reason='CPU DECODER IS ORIGINAL, NOT v23 (ROM='..rom_state..')'
    else
        reason='INCONCLUSIVE: ROM='..rom_state..'; CPU='..cpu_state
    end
end
rescan()

local function note(line)
    if #observations < MAX_OBSERVATIONS then
        observations[#observations+1] = line
    end
end
local function verdict()
    if not valid then return 'DECODER NOT VERIFIED: ' .. reason end
    if counters.bad_high > 0 then return 'UNEXPECTED HIGH BYTE >= ED IN READER' end
    if counters.token_candidates == 0 then
        if counters.reads == 0 then return 'INTRO/NO BANK 6 READER HIT YET' end
        return 'BANK 6 READ, NO TOKEN ENCOUNTERED YET'
    end
    if counters.resolver < counters.token_candidates then
        return 'WARNING: TOKEN SEEN WITHOUT MATCHING RESOLVER'
    end
    if counters.secondary == 0 then
        return 'TOKEN RESOLVER HIT; SECONDARY READER NOT SEEN'
    end
    return 'TOKEN PATH EXECUTED (VISUAL OUTPUT STILL TO CHECK)'
end
local function report()
    local ok, f = pcall(io.open, OUT, 'w')
    if not ok or not f then write_problem = true; return end
    f:write('Square no Tom Sawyer - v24b decoder execution trace\n')
    f:write('Experimental v23 ROM fingerprint: ', tostring(valid), '\n')
    f:write('Fingerprint explanation: ', reason, '\n')
    f:write('ROM file decoder bytes: ', rom_state, '\n')
    f:write('CPU mapped decoder bytes: ', cpu_state, '\n')
    f:write('Fingerprint checks: ', retries, '\n')
    f:write('Elapsed frames: ', tostring(emu.framecount()-frame_start), '\n')
    f:write('Bank6 dispatch at EDE7: ', counters.reads, '\n')
    f:write('Token candidates D0-EC: ', counters.token_candidates, '\n')
    f:write('Unexpected >=ED bytes: ', counters.bad_high, '\n')
    f:write('Token resolver EDFD: ', counters.resolver, '\n')
    f:write('Secondary reader EE2C: ', counters.secondary, '\n')
    f:write('Last token: ', last_token, '\n')
    f:write('STATUS: ', verdict(), '\n')
    f:write('Distinct observed tokens:\n')
    for b=D0,EC do
        if token_counts[b] then
            f:write(string.format('  $%02X target B6-%03d: %d hits\n',
                b,b-D0,token_counts[b]))
        end
    end
    f:write('First observations:\n')
    for _,row in ipairs(observations) do f:write(row, '\n') end
    f:write('IMPORTANT: The Bank8 English intro cannot validate Bank6 tokens.\n')
    f:write('Hook count is execution evidence, not proof of correct rendered output.\n')
    f:close()
    last_write=emu.framecount()
end

-- Hook source CPU addresses in fixed PRG bank 15; no RAM/ROM writes.
memory.registerexec(0xEDE7, function()
    if not valid then return end
    local a=memory.getregister('a')
    counters.reads=counters.reads+1
    if a>=D0 and a<=EC then
        counters.token_candidates=counters.token_candidates+1
        token_counts[a]=(token_counts[a] or 0)+1
        last_token=string.format('$%02X (shared B6-%03d)',a,a-D0)
        note(string.format('frame=%d dispatch A=%02X token=%02X',emu.framecount(),a,a))
    elseif a>=0xED then
        counters.bad_high=counters.bad_high+1
        note(string.format('frame=%d BAD high A=%02X',emu.framecount(),a))
    end
end)
memory.registerexec(0xEDFD, function()
    if not valid then return end
    counters.resolver=counters.resolver+1
    local a=memory.getregister('a')
    note(string.format('frame=%d resolver A=%02X',emu.framecount(),a))
end)
memory.registerexec(0xEE2C, function()
    if valid then counters.secondary=counters.secondary+1 end
end)

emu.registerexit(report)
report()
while true do
    local elapsed=emu.framecount()-frame_start
    if elapsed>0 and elapsed%60==0 then rescan() end
    gui.text(2,2,'STS v24b - v23: '..(valid and 'YES' or 'UNCONFIRMED'))
    gui.text(2,12,string.format('Bank6: %d  token: %d  resolver: %d',
        counters.reads,counters.token_candidates,counters.resolver))
    gui.text(2,22,'ref reader: '..counters.secondary..'  bad high: '..counters.bad_high)
    if valid and counters.token_candidates==0 then
        gui.text(2,32,'Intro only = no token proof. Trigger ONE LOOK/NPC response.')
    else
        gui.text(2,32,verdict())
    end
    gui.text(2,42,'File: '..rom_state..' CPU: '..cpu_state)
    if write_problem then gui.text(2,52,'Log write failed; send counters screenshot.') end
    if elapsed>0 and emu.framecount()-last_write>=120 then report() end
    emu.frameadvance()
end
